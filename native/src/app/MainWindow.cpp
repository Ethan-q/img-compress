#include "MainWindow.h"

#include <QCheckBox>
#include <QComboBox>
#include <QFileDialog>
#include <QFormLayout>
#include <QGroupBox>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QProgressBar>
#include <QSlider>
#include <QVBoxLayout>

#include "core/CompressController.h"

MainWindow::MainWindow(QWidget *parent) : QMainWindow(parent) {
    setupUi();
    controller = new CompressController(this);
    connect(controller, &CompressController::logMessage, this, &MainWindow::onLogMessage);
    connect(controller, &CompressController::progressChanged, this, &MainWindow::onProgressChanged);
    connect(controller, &CompressController::finished, this, &MainWindow::onFinished);
}

void MainWindow::setupUi() {
    setWindowTitle("Imgcompress Native");
    resize(900, 600);

    auto *central = new QWidget(this);
    auto *rootLayout = new QVBoxLayout();

    auto *pathGroup = new QGroupBox("路径", this);
    auto *pathLayout = new QFormLayout();
    auto *inputLayout = new QHBoxLayout();
    inputLine = new QLineEdit(this);
    auto *inputButton = new QPushButton("选择输入目录", this);
    connect(inputButton, &QPushButton::clicked, this, &MainWindow::pickInputDir);
    inputLayout->addWidget(inputLine);
    inputLayout->addWidget(inputButton);
    pathLayout->addRow("输入目录", inputLayout);

    auto *outputLayout = new QHBoxLayout();
    outputLine = new QLineEdit(this);
    auto *outputButton = new QPushButton("选择输出目录", this);
    connect(outputButton, &QPushButton::clicked, this, &MainWindow::pickOutputDir);
    outputLayout->addWidget(outputLine);
    outputLayout->addWidget(outputButton);
    pathLayout->addRow("输出目录", outputLayout);
    pathGroup->setLayout(pathLayout);

    auto *optionsGroup = new QGroupBox("压缩选项", this);
    auto *optionsLayout = new QFormLayout();
    losslessCheck = new QCheckBox("无损压缩", this);
    profileCombo = new QComboBox(this);
    profileCombo->addItems({"高质量(推荐)", "均衡", "强压缩"});
    qualitySlider = new QSlider(Qt::Horizontal, this);
    qualitySlider->setRange(10, 100);
    qualitySlider->setValue(85);
    qualityValue = new QLabel("85", this);
    connect(qualitySlider, &QSlider::valueChanged, this, [this](int value) {
        qualityValue->setText(QString::number(value));
    });
    auto *qualityLayout = new QHBoxLayout();
    qualityLayout->addWidget(qualitySlider);
    qualityLayout->addWidget(qualityValue);
    optionsLayout->addRow(losslessCheck);
    optionsLayout->addRow("压缩预设", profileCombo);
    optionsLayout->addRow("有损质量", qualityLayout);

    auto *formatLayout = new QHBoxLayout();
    formatJpg = new QCheckBox("JPG", this);
    formatPng = new QCheckBox("PNG", this);
    formatGif = new QCheckBox("GIF", this);
    formatWebp = new QCheckBox("WebP", this);
    formatJpg->setChecked(true);
    formatPng->setChecked(true);
    formatGif->setChecked(true);
    formatWebp->setChecked(true);
    formatLayout->addWidget(formatJpg);
    formatLayout->addWidget(formatPng);
    formatLayout->addWidget(formatGif);
    formatLayout->addWidget(formatWebp);
    optionsLayout->addRow("格式", formatLayout);
    optionsGroup->setLayout(optionsLayout);

    startButton = new QPushButton("开始压缩", this);
    connect(startButton, &QPushButton::clicked, this, &MainWindow::startCompression);

    progressBar = new QProgressBar(this);
    progressBar->setValue(0);

    logArea = new QPlainTextEdit(this);
    logArea->setReadOnly(true);

    rootLayout->addWidget(pathGroup);
    rootLayout->addWidget(optionsGroup);
    rootLayout->addWidget(startButton);
    rootLayout->addWidget(progressBar);
    rootLayout->addWidget(logArea);

    central->setLayout(rootLayout);
    setCentralWidget(central);
}

void MainWindow::pickInputDir() {
    const QString dir = QFileDialog::getExistingDirectory(this, "选择输入目录");
    if (!dir.isEmpty()) {
        inputLine->setText(dir);
    }
}

void MainWindow::pickOutputDir() {
    const QString dir = QFileDialog::getExistingDirectory(this, "选择输出目录");
    if (!dir.isEmpty()) {
        outputLine->setText(dir);
    }
}

void MainWindow::startCompression() {
    const QString inputDir = inputLine->text().trimmed();
    QString outputDir = outputLine->text().trimmed();
    QStringList formats;
    if (formatJpg->isChecked()) {
        formats << "jpg" << "jpeg";
    }
    if (formatPng->isChecked()) {
        formats << "png";
    }
    if (formatGif->isChecked()) {
        formats << "gif";
    }
    if (formatWebp->isChecked()) {
        formats << "webp";
    }
    if (outputDir.isEmpty()) {
        outputDir = inputDir;
    }
    controller->start(
        inputDir,
        outputDir,
        formats,
        losslessCheck->isChecked(),
        qualitySlider->value(),
        profileCombo->currentText()
    );
    startButton->setEnabled(false);
    progressBar->setValue(0);
}

void MainWindow::onLogMessage(const QString &message) {
    logArea->appendPlainText(message);
}

void MainWindow::onProgressChanged(int percent) {
    progressBar->setValue(percent);
}

void MainWindow::onFinished() {
    progressBar->setValue(100);
    startButton->setEnabled(true);
}
