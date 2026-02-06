#include "EngineRegistry.h"

#include <QCoreApplication>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QPair>
#include <QProcess>
#include <QSysInfo>

namespace {
QString normalizeProfile(const QString &profile) {
    if (profile.contains("强")) {
        return "strong";
    }
    if (profile.contains("均衡")) {
        return "balanced";
    }
    if (profile == "strong" || profile == "balanced" || profile == "high") {
        return profile;
    }
    return "high";
}

int adjustQuality(int quality, const QString &profile) {
    const QString normalized = normalizeProfile(profile);
    if (normalized == "strong") {
        return qMax(10, quality - 10);
    }
    if (normalized == "balanced") {
        return qMax(10, quality - 4);
    }
    return quality;
}

QPair<int, int> getPngquantSettings(const QString &profile, int quality) {
    const QString normalized = normalizeProfile(profile);
    int rangeSize = 8;
    int speed = 1;
    if (normalized == "strong") {
        rangeSize = 25;
        speed = 3;
    } else if (normalized == "balanced") {
        rangeSize = 15;
        speed = 2;
    }
    const int minQ = qMax(10, quality - rangeSize);
    return qMakePair(minQ, speed);
}

int adjustLossy(const QString &profile, int lossy) {
    const QString normalized = normalizeProfile(profile);
    if (normalized == "strong") {
        return qMin(200, static_cast<int>(lossy * 1.4));
    }
    if (normalized == "balanced") {
        return qMin(200, static_cast<int>(lossy * 1.1));
    }
    return lossy;
}

int adjustColors(const QString &profile, int colors) {
    const QString normalized = normalizeProfile(profile);
    if (normalized == "strong") {
        return qMax(16, static_cast<int>(colors * 0.7));
    }
    if (normalized == "balanced") {
        return qMax(16, static_cast<int>(colors * 0.85));
    }
    return colors;
}

QString detectPlatform() {
    if (QSysInfo::productType() == "osx") {
        return "macos";
    }
    if (QSysInfo::productType() == "windows") {
        return "windows";
    }
    return "linux";
}

QString detectArch() {
    const QString arch = QSysInfo::currentCpuArchitecture().toLower();
    if (arch.contains("arm64") || arch.contains("aarch64")) {
        return "arm64";
    }
    if (arch.contains("x86_64") || arch.contains("amd64")) {
        return "x64";
    }
    return arch;
}

QString findTool(const QStringList &names) {
    const QString appDir = QCoreApplication::applicationDirPath();
    const QString platformKey = detectPlatform();
    const QString archKey = detectArch();
    const QStringList baseDirs = {
        appDir,
        QDir(appDir).filePath("vendor"),
        QDir(appDir).filePath(QString("vendor/%1/%2").arg(platformKey, archKey)),
        QDir(appDir).filePath(QString("vendor/%1").arg(platformKey)),
        QDir(appDir).filePath("../Resources"),
        QDir(appDir).filePath("../Resources/vendor"),
        QDir(appDir).filePath(QString("../Resources/vendor/%1/%2").arg(platformKey, archKey)),
        QDir(appDir).filePath(QString("../Resources/vendor/%1").arg(platformKey)),
        QDir(appDir).filePath("../MacOS"),
        QDir(appDir).filePath("../MacOS/vendor"),
        QDir(appDir).filePath(QString("../MacOS/vendor/%1/%2").arg(platformKey, archKey)),
        QDir(appDir).filePath(QString("../MacOS/vendor/%1").arg(platformKey)),
        QDir(appDir).filePath("../Frameworks"),
        QDir(appDir).filePath("../Frameworks/vendor"),
        QDir(appDir).filePath(QString("../Frameworks/vendor/%1/%2").arg(platformKey, archKey)),
        QDir(appDir).filePath(QString("../Frameworks/vendor/%1").arg(platformKey)),
    };
    for (const QString &base : baseDirs) {
        for (const QString &name : names) {
            const QString candidate = QDir(base).filePath(name);
            if (QFileInfo::exists(candidate)) {
                return candidate;
            }
            const QString exeCandidate = QDir(base).filePath(name + ".exe");
            if (QFileInfo::exists(exeCandidate)) {
                return exeCandidate;
            }
        }
    }
    return {};
}

bool runProcess(const QString &program, const QStringList &args) {
    QProcess process;
    process.setProgram(program);
    process.setArguments(args);
    process.setProcessChannelMode(QProcess::MergedChannels);
    process.start();
    process.waitForFinished(-1);
    return process.exitStatus() == QProcess::NormalExit && process.exitCode() == 0;
}

CompressionResult copyOriginal(const QString &source, const QString &output) {
    QFile::remove(output);
    QFile::copy(source, output);
    const qint64 originalSize = QFileInfo(source).size();
    const qint64 outputSize = QFileInfo(output).size();
    return {true, originalSize, outputSize, "原图", "缺少引擎，已保留原图"};
}
}

QStringList EngineRegistry::availableEngines() {
    return {"jpegtran", "mozjpeg", "pngquant", "oxipng", "optipng", "gifsicle", "cwebp"};
}

CompressionResult EngineRegistry::compressFile(
    const QString &source,
    const QString &output,
    const CompressionOptions &options
) {
    const QString suffix = QFileInfo(source).suffix().toLower();
    const qint64 originalSize = QFileInfo(source).size();
    if (suffix == "jpg" || suffix == "jpeg") {
        if (options.lossless) {
            const QString jpegtran = findTool({"jpegtran"});
            if (jpegtran.isEmpty()) {
                return copyOriginal(source, output);
            }
            const QStringList args = {
                "-copy",
                "none",
                "-optimize",
                "-progressive",
                "-outfile",
                output,
                source
            };
            const bool ok = runProcess(jpegtran, args);
            const qint64 outputSize = QFileInfo(output).size();
            return {ok, originalSize, outputSize, "jpegtran", ok ? "成功" : "失败"};
        }
        const QString cjpeg = findTool({"cjpeg", "mozjpeg"});
        if (cjpeg.isEmpty()) {
            return copyOriginal(source, output);
        }
        const int quality = qBound(1, adjustQuality(options.quality, options.profile), 100);
        const QStringList args = {
            "-quality",
            QString::number(quality),
            "-progressive",
            "-optimize",
            "-outfile",
            output,
            source
        };
        const bool ok = runProcess(cjpeg, args);
        const qint64 outputSize = QFileInfo(output).size();
        return {ok, originalSize, outputSize, "mozjpeg", ok ? "成功" : "失败"};
    }
    if (suffix == "png") {
        if (!options.lossless) {
            const QString pngquant = findTool({"pngquant"});
            if (!pngquant.isEmpty()) {
                const int quality = qBound(10, adjustQuality(options.quality, options.profile), 100);
                const auto settings = getPngquantSettings(options.profile, quality);
                const QStringList args = {
                    "--quality",
                    QString("%1-%2").arg(settings.first).arg(quality),
                    "--speed",
                    QString::number(settings.second),
                    "--strip",
                    "--skip-if-larger",
                    "--output",
                    output,
                    "--force",
                    source
                };
                const bool ok = runProcess(pngquant, args);
                const qint64 outputSize = QFileInfo(output).size();
                if (ok) {
                    return {true, originalSize, outputSize, "pngquant", "成功"};
                }
            }
        }
        const QString optimizer = findTool({"oxipng", "optipng"});
        if (optimizer.isEmpty()) {
            return copyOriginal(source, output);
        }
        QStringList args;
        if (optimizer.contains("oxipng")) {
            args = {"-o", "4", "--strip", "all", "-out", output, source};
        } else {
            args = {"-o7", "-strip", "all", "-out", output, source};
        }
        const bool ok = runProcess(optimizer, args);
        const qint64 outputSize = QFileInfo(output).size();
        return {ok, originalSize, outputSize, optimizer.contains("oxipng") ? "oxipng" : "optipng", ok ? "成功" : "失败"};
    }
    if (suffix == "gif") {
        const QString gifsicle = findTool({"gifsicle"});
        if (gifsicle.isEmpty()) {
            return copyOriginal(source, output);
        }
        QStringList args = {"-O3", "--no-comments", "--no-names", "--no-extensions"};
        if (!options.lossless) {
            const int quality = qBound(1, adjustQuality(options.quality, options.profile), 100);
            int lossy = qMax(0, static_cast<int>((100 - quality) * 2));
            lossy = adjustLossy(options.profile, lossy);
            int colors = qMax(32, static_cast<int>(256 * quality / 100));
            colors = adjustColors(options.profile, colors);
            args << "--lossy" << QString::number(lossy) << "--colors" << QString::number(colors);
        }
        args << source << "-o" << output;
        const bool ok = runProcess(gifsicle, args);
        const qint64 outputSize = QFileInfo(output).size();
        return {ok, originalSize, outputSize, "gifsicle", ok ? "成功" : "失败"};
    }
    if (suffix == "webp") {
        const QString cwebp = findTool({"cwebp"});
        if (cwebp.isEmpty()) {
            return copyOriginal(source, output);
        }
        QStringList args;
        if (options.lossless) {
            args = {"-lossless", "-z", "9", "-m", "6", "-metadata", "none", source, "-o", output};
        } else {
            const int quality = qBound(1, adjustQuality(options.quality, options.profile), 100);
            args = {"-q", QString::number(quality), "-m", "6", "-metadata", "none", source, "-o", output};
        }
        const bool ok = runProcess(cwebp, args);
        const qint64 outputSize = QFileInfo(output).size();
        return {ok, originalSize, outputSize, "cwebp", ok ? "成功" : "失败"};
    }
    return {false, originalSize, originalSize, "无", "不支持的格式"};
}
