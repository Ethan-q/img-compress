#pragma once

#include <QMainWindow>

class QLineEdit;
class QPushButton;
class QCheckBox;
class QComboBox;
class QSlider;
class QLabel;
class QPlainTextEdit;
class QProgressBar;

class CompressController;

class MainWindow final : public QMainWindow {
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);

private slots:
    void pickInputDir();
    void pickOutputDir();
    void startCompression();
    void onLogMessage(const QString &message);
    void onProgressChanged(int percent);
    void onFinished();

private:
    void setupUi();

    QLineEdit *inputLine;
    QLineEdit *outputLine;
    QCheckBox *losslessCheck;
    QComboBox *profileCombo;
    QSlider *qualitySlider;
    QLabel *qualityValue;
    QCheckBox *formatJpg;
    QCheckBox *formatPng;
    QCheckBox *formatGif;
    QCheckBox *formatWebp;
    QPushButton *startButton;
    QProgressBar *progressBar;
    QPlainTextEdit *logArea;
    CompressController *controller;
};
