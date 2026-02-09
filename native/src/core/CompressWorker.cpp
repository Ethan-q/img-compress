#include "CompressWorker.h"

#include <QDateTime>
#include <QDir>
#include <QDirIterator>
#include <QFile>
#include <QFileInfo>
#include <QImage>
#include <QImageReader>
#include <QImageWriter>
#include <QSet>
#include <QTemporaryFile>

namespace {
QString ensureUniquePath(const QString &candidate, const QString &sourcePath, const QString &stem, const QString &suffix) {
    const QFileInfo candidateInfo(candidate);
    const QFileInfo sourceInfo(sourcePath);
    const QString candidatePath = candidateInfo.absoluteFilePath();
    const QString sourceAbsPath = sourceInfo.absoluteFilePath();
    if (candidatePath != sourceAbsPath && !QFileInfo::exists(candidatePath)) {
        return candidatePath;
    }
    const QString ext = suffix.isEmpty() ? QString() : "." + suffix;
    QDir dir = candidateInfo.dir();
    int index = 1;
    while (true) {
        const QString name = QString("%1(%2)%3").arg(stem).arg(index).arg(ext);
        const QString nextPath = dir.filePath(name);
        if (!QFileInfo::exists(nextPath) && nextPath != sourceAbsPath) {
            return nextPath;
        }
        index += 1;
    }
}

int adjustQuality(int quality, const QString &profile) {
    if (profile.contains("强")) {
        return qMax(8, quality - 18);
    }
    if (profile.contains("均衡")) {
        return qMax(10, quality - 10);
    }
    return quality;
}
}

CompressWorker::CompressWorker(QObject *parent) : QObject(parent), useFileList(false) {}

void CompressWorker::configure(
    const QString &inputDirValue,
    const QString &outputDirValue,
    const QStringList &formatsValue,
    const CompressionOptions &optionsValue
) {
    inputDir = inputDirValue;
    outputDir = outputDirValue;
    formats = formatsValue;
    options = optionsValue;
    files.clear();
    useFileList = false;
}

void CompressWorker::configureFiles(
    const QStringList &filesValue,
    const QString &baseDir,
    const QString &outputDirValue,
    const QStringList &formatsValue,
    const CompressionOptions &optionsValue
) {
    inputDir = baseDir;
    outputDir = outputDirValue;
    formats = formatsValue;
    options = optionsValue;
    files = filesValue;
    useFileList = true;
}

void CompressWorker::run() {
    QStringList filters;
    for (const QString &fmt : formats) {
        filters << QString("*.%1").arg(fmt.toLower());
    }
    QStringList workingFiles;
    QSet<QString> formatSet;
    for (const QString &fmt : formats) {
        formatSet.insert(fmt.toLower());
    }
    if (useFileList) {
        for (const QString &file : files) {
            const QString suffix = QFileInfo(file).suffix().toLower();
            if (formatSet.contains(suffix)) {
                workingFiles.append(file);
            }
        }
    } else {
        QDirIterator it(inputDir, filters, QDir::Files, QDirIterator::Subdirectories);
        while (it.hasNext()) {
            workingFiles.append(it.next());
        }
    }
    if (workingFiles.isEmpty()) {
        emit logMessage("未找到可压缩图片");
        emit finished(0, 0, 0, 0);
        return;
    }
    emit logMessage(QString("开始压缩 %1 张图片").arg(workingFiles.size()));
    const QDateTime started = QDateTime::currentDateTime();
    int successCount = 0;
    qint64 totalBefore = 0;
    qint64 totalAfter = 0;
    QDir inputRoot(inputDir);
    QDir outputRoot(outputDir);
    int completed = 0;
    for (const QString &file : workingFiles) {
        const QFileInfo sourceInfo(file);
        const QString relativePath = inputRoot.relativeFilePath(file);
        const QFileInfo relativeInfo(relativePath);
        const QString sourceSuffix = sourceInfo.suffix().toLower();
        const QByteArray detectedFormat = QImageReader::imageFormat(file);
        const QString actualSuffix = QString::fromLatin1(detectedFormat).toLower();
        if (!actualSuffix.isEmpty() && actualSuffix != sourceSuffix) {
            emit logMessage(
                QString("%1 实际格式为 %2，与扩展名 %3 不一致")
                    .arg(sourceInfo.fileName())
                    .arg(actualSuffix)
                    .arg(sourceSuffix)
            );
        }
        const QString targetFormat = options.outputFormat.isEmpty() || options.outputFormat == "original"
            ? (!actualSuffix.isEmpty() ? actualSuffix : sourceSuffix)
            : options.outputFormat.toLower();
        const QString baseName = sourceInfo.completeBaseName();
        const QString relativeDir = relativeInfo.path();
        const QString outputFileName = targetFormat.isEmpty() ? baseName : baseName + "." + targetFormat;
        QString outputPath = relativeDir == "."
            ? outputRoot.filePath(outputFileName)
            : outputRoot.filePath(relativeDir + "/" + outputFileName);
        outputPath = ensureUniquePath(outputPath, sourceInfo.absoluteFilePath(), baseName, targetFormat);
        QFileInfo outputInfo(outputPath);
        QDir outputDirInfo = outputInfo.dir();
        if (!outputDirInfo.exists()) {
            outputDirInfo.mkpath(".");
        }
        const qint64 sourceSize = sourceInfo.size();
        CompressionResult result{false, sourceSize, sourceSize, "无", "失败"};
        const bool convertToWebp = targetFormat == "webp" && (actualSuffix.isEmpty() ? sourceSuffix : actualSuffix) != "webp";
        const bool convertToGif = targetFormat == "gif" && (actualSuffix.isEmpty() ? sourceSuffix : actualSuffix) != "gif";
        const bool convertFromWebp = (actualSuffix.isEmpty() ? sourceSuffix : actualSuffix) == "webp"
            && (targetFormat == "jpg" || targetFormat == "jpeg" || targetFormat == "png");
        if (convertToGif) {
            emit logMessage(QString("%1 转换失败：不支持转换为GIF").arg(sourceInfo.fileName()));
            completed += 1;
            emit progressChanged(static_cast<int>((static_cast<double>(completed) / workingFiles.size()) * 100.0));
            continue;
        }
        if (options.resizeEnabled && ((actualSuffix.isEmpty() ? sourceSuffix : actualSuffix) == "webp" || targetFormat == "webp")) {
            emit logMessage(QString("%1 转换失败：启用尺寸裁剪/缩放时不支持 WebP（需要 Qt WebP 插件）").arg(sourceInfo.fileName()));
            completed += 1;
            emit progressChanged(static_cast<int>((static_cast<double>(completed) / workingFiles.size()) * 100.0));
            continue;
        }
        if ((convertToWebp || convertFromWebp) && !options.resizeEnabled) {
            result = EngineRegistry::compressFile(file, outputPath, options);
            if (!result.success) {
                QImageReader reader(file);
                reader.setAutoTransform(true);
                if (!actualSuffix.isEmpty()) {
                    reader.setFormat(actualSuffix.toLatin1());
                }
                QImage image = reader.read();
                if (!image.isNull()) {
                    QString tempFormat = !actualSuffix.isEmpty() ? actualSuffix : "png";
                    QTemporaryFile temp(outputRoot.filePath(".imgcompress_tmp_XXXXXX." + tempFormat));
                    temp.setAutoRemove(true);
                    if (temp.open()) {
                        const QString tempPath = temp.fileName();
                        temp.close();
                        QImageWriter writer(tempPath, tempFormat.toLatin1());
                        const int quality = options.lossless
                            ? 100
                            : qBound(1, adjustQuality(options.quality, options.profile), 100);
                        writer.setQuality(quality);
                        if (writer.write(image)) {
                            result = EngineRegistry::compressFile(tempPath, outputPath, options);
                            if (!result.success) {
                                QFile::remove(outputPath);
                                QFile::copy(tempPath, outputPath);
                                result = {true, sourceSize, QFileInfo(outputPath).size(), "Qt", "已转换"};
                            } else {
                                result.originalSize = sourceSize;
                                result.outputSize = QFileInfo(outputPath).size();
                            }
                        } else {
                            emit logMessage(QString("%1 转换失败：无法写入格式").arg(sourceInfo.fileName()));
                        }
                    } else {
                        emit logMessage(QString("%1 转换失败：无法创建临时文件").arg(sourceInfo.fileName()));
                    }
                }
            }
        } else if (options.resizeEnabled || targetFormat != (actualSuffix.isEmpty() ? sourceSuffix : actualSuffix)) {
            QImageReader reader(file);
            reader.setAutoTransform(true);
            if ((actualSuffix.isEmpty() ? sourceSuffix : actualSuffix) == "webp") {
                reader.setFormat("webp");
            }
            QImage image = reader.read();
            if (image.isNull()) {
                if ((actualSuffix.isEmpty() ? sourceSuffix : actualSuffix) == "webp") {
                    emit logMessage(QString("%1 转换失败：WebP 解码不可用（缺少 dwebp 或 Qt WebP 插件）").arg(sourceInfo.fileName()));
                } else {
                    emit logMessage(QString("%1 转换失败：无法读取图片").arg(sourceInfo.fileName()));
                }
                completed += 1;
                emit progressChanged(static_cast<int>((static_cast<double>(completed) / workingFiles.size()) * 100.0));
                continue;
            }
            if (options.resizeEnabled) {
                if (options.resizeMode == 2) {
                    image = image.scaled(
                        options.targetWidth,
                        options.targetHeight,
                        Qt::KeepAspectRatioByExpanding,
                        Qt::SmoothTransformation
                    );
                    const int cropWidth = qMin(options.targetWidth, image.width());
                    const int cropHeight = qMin(options.targetHeight, image.height());
                    const int offsetX = qMax(0, (image.width() - cropWidth) / 2);
                    const int offsetY = qMax(0, (image.height() - cropHeight) / 2);
                    image = image.copy(QRect(offsetX, offsetY, cropWidth, cropHeight));
                } else if (options.resizeMode == 1) {
                    image = image.scaled(
                        options.targetWidth,
                        options.targetHeight,
                        Qt::KeepAspectRatio,
                        Qt::SmoothTransformation
                    );
                }
            }
            QString tempFormat = targetFormat;
            bool allowTempFallback = true;
            if (convertToWebp || convertToGif) {
                tempFormat = (!actualSuffix.isEmpty() ? actualSuffix : (sourceSuffix.isEmpty() ? "png" : sourceSuffix));
                allowTempFallback = false;
            }
            QTemporaryFile temp(outputRoot.filePath(".imgcompress_tmp_XXXXXX." + tempFormat));
            temp.setAutoRemove(true);
            if (!temp.open()) {
                emit logMessage(QString("%1 转换失败：无法创建临时文件").arg(sourceInfo.fileName()));
                completed += 1;
                emit progressChanged(static_cast<int>((static_cast<double>(completed) / workingFiles.size()) * 100.0));
                continue;
            }
            const QString tempPath = temp.fileName();
            temp.close();
            QImageWriter writer(tempPath, tempFormat.toLatin1());
            const int quality = options.lossless
                ? 100
                : qBound(1, adjustQuality(options.quality, options.profile), 100);
            writer.setQuality(quality);
            if (!writer.write(image)) {
                emit logMessage(QString("%1 转换失败：无法写入格式").arg(sourceInfo.fileName()));
                completed += 1;
                emit progressChanged(static_cast<int>((static_cast<double>(completed) / workingFiles.size()) * 100.0));
                continue;
            }
            result = EngineRegistry::compressFile(tempPath, outputPath, options);
            if (!result.success && allowTempFallback) {
                QFile::remove(outputPath);
                QFile::copy(tempPath, outputPath);
                result = {true, sourceSize, QFileInfo(outputPath).size(), "Qt", "已转换"};
            } else {
                result.originalSize = sourceSize;
                result.outputSize = QFileInfo(outputPath).size();
            }
        } else {
            result = EngineRegistry::compressFile(file, outputPath, options);
        }
        if (result.success) {
            if (result.outputSize > result.originalSize) {
                QFile::remove(outputPath);
                QFile::copy(sourceInfo.absoluteFilePath(), outputPath);
                result.outputSize = QFileInfo(outputPath).size();
                result.engine = "原图";
                result.message = "已保留原图";
            }
            successCount += 1;
            totalBefore += result.originalSize;
            totalAfter += result.outputSize;
            const double ratio = result.originalSize > 0
                ? 1.0 - (static_cast<double>(result.outputSize) / result.originalSize)
                : 0.0;
            emit logMessage(
                QString("%1 压缩完成，节省 %2，引擎 %3")
                    .arg(QFileInfo(file).fileName())
                    .arg(QString::number(ratio * 100.0, 'f', 1) + "%")
                    .arg(result.engine)
            );
        } else {
            emit logMessage(
                QString("%1 压缩失败：%2")
                    .arg(QFileInfo(file).fileName())
                    .arg(result.message)
            );
        }
        completed += 1;
        const int percent = static_cast<int>((static_cast<double>(completed) / workingFiles.size()) * 100.0);
        emit progressChanged(percent);
    }
    const qint64 saved = totalBefore - totalAfter;
    const double totalRatio = totalBefore > 0
        ? static_cast<double>(saved) / totalBefore
        : 0.0;
    const qint64 elapsedMs = started.msecsTo(QDateTime::currentDateTime());
    emit logMessage(
        QString("完成：成功 %1 张，节省 %2，用时 %3 秒")
            .arg(successCount)
            .arg(QString::number(totalRatio * 100.0, 'f', 1) + "%")
            .arg(QString::number(elapsedMs / 1000.0, 'f', 1))
    );
    emit finished(successCount, totalBefore, totalAfter, elapsedMs);
}
