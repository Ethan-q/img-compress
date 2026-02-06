#include "CompressWorker.h"

#include <QDateTime>
#include <QDir>
#include <QDirIterator>
#include <QFileInfo>

CompressWorker::CompressWorker(QObject *parent) : QObject(parent) {}

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
}

void CompressWorker::run() {
    QStringList filters;
    for (const QString &fmt : formats) {
        filters << QString("*.%1").arg(fmt.toLower());
    }
    QDirIterator it(inputDir, filters, QDir::Files, QDirIterator::Subdirectories);
    QList<QString> files;
    while (it.hasNext()) {
        files.append(it.next());
    }
    if (files.isEmpty()) {
        emit logMessage("未找到可压缩图片");
        emit finished(0, 0, 0, 0);
        return;
    }
    emit logMessage(QString("开始压缩 %1 张图片").arg(files.size()));
    const QDateTime started = QDateTime::currentDateTime();
    int successCount = 0;
    qint64 totalBefore = 0;
    qint64 totalAfter = 0;
    QDir inputRoot(inputDir);
    QDir outputRoot(outputDir);
    int completed = 0;
    for (const QString &file : files) {
        const QString relativePath = inputRoot.relativeFilePath(file);
        const QString outputPath = outputRoot.filePath(relativePath);
        QFileInfo outputInfo(outputPath);
        QDir outputDirInfo = outputInfo.dir();
        if (!outputDirInfo.exists()) {
            outputDirInfo.mkpath(".");
        }
        const CompressionResult result = EngineRegistry::compressFile(file, outputPath, options);
        if (result.success) {
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
        const int percent = static_cast<int>((static_cast<double>(completed) / files.size()) * 100.0);
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
