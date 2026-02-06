#pragma once

#include <QObject>
#include <QString>
#include <QStringList>

#include "engine/EngineRegistry.h"

class CompressWorker final : public QObject {
    Q_OBJECT

public:
    explicit CompressWorker(QObject *parent = nullptr);

    void configure(
        const QString &inputDir,
        const QString &outputDir,
        const QStringList &formats,
        const CompressionOptions &options
    );

public slots:
    void run();

signals:
    void progressChanged(int percent);
    void logMessage(const QString &message);
    void finished(int successCount, qint64 totalBefore, qint64 totalAfter, qint64 elapsedMs);

private:
    QString inputDir;
    QString outputDir;
    QStringList formats;
    CompressionOptions options;
};
