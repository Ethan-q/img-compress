#pragma once

#include <QtGlobal>
#include <QString>
#include <QStringList>

struct CompressionOptions {
    bool lossless;
    int quality;
    QString profile;
};

struct CompressionResult {
    bool success;
    qint64 originalSize;
    qint64 outputSize;
    QString engine;
    QString message;
};

class EngineRegistry {
public:
    static QStringList availableEngines();
    static CompressionResult compressFile(
        const QString &source,
        const QString &output,
        const CompressionOptions &options
    );
};
