#include "MainWindow.h"

#include <QAbstractItemView>
#include <QCheckBox>
#include <QComboBox>
#include <QColor>
#include <QDir>
#include <QDirIterator>
#include <QDragEnterEvent>
#include <QDragLeaveEvent>
#include <QDropEvent>
#include <QFileDialog>
#include <QFileInfo>
#include <QFormLayout>
#include <QFrame>
#include <QGridLayout>
#include <QGroupBox>
#include <QHBoxLayout>
#include <QIntValidator>
#include <QLabel>
#include <QLineEdit>
#include <QListView>
#include <QMimeData>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QProgressBar>
#include <QSizePolicy>
#include <QSlider>
#include <QSpinBox>
#include <QSet>
#include <QTextCharFormat>
#include <QTextCursor>
#include <QTextEdit>
#include <QTextDocument>
#include <QThread>
#include <QUrl>
#include <QVBoxLayout>

#include <algorithm>

#include "core/CompressController.h"

DropArea::DropArea(QWidget *parent) : QFrame(parent) {
    setAcceptDrops(true);
    setMinimumHeight(240);
    setStyleSheet(QStringLiteral(
        "QFrame {"
        " border: 1px dashed #cbd5f5;"
        " border-radius: 14px;"
        " background: #ffffff;"
        "}"
    ));
    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(16, 24, 16, 24);
    layout->setSpacing(0);
    auto *title = new QLabel("拖拽图片/文件夹到此处开始压缩（输出同目录）", this);
    title->setAlignment(Qt::AlignCenter);
    title->setStyleSheet("color: #111827; font-size: 15px; font-weight: 600;");
    layout->addWidget(title);
}

void DropArea::dragEnterEvent(QDragEnterEvent *event) {
    if (event->mimeData()->hasUrls()) {
        event->acceptProposedAction();
        setStyleSheet(QStringLiteral(
            "QFrame {"
        " border: 1px dashed #3b82f6;"
            " border-radius: 14px;"
            " background: #eff6ff;"
            "}"
        ));
        return;
    }
    event->ignore();
}

void DropArea::dragLeaveEvent(QDragLeaveEvent *event) {
    QFrame::dragLeaveEvent(event);
    setStyleSheet(QStringLiteral(
        "QFrame {"
        " border: 1px dashed #cbd5f5;"
        " border-radius: 14px;"
        " background: #ffffff;"
        "}"
    ));
}

void DropArea::dropEvent(QDropEvent *event) {
    if (!event->mimeData()->hasUrls()) {
        event->ignore();
        return;
    }
    QStringList paths;
    const QList<QUrl> urls = event->mimeData()->urls();
    for (const QUrl &url : urls) {
        const QString local = url.toLocalFile();
        if (!local.isEmpty()) {
            paths << local;
        }
    }
    if (!paths.isEmpty()) {
        emit dropped(paths);
    }
    setStyleSheet(QStringLiteral(
        "QFrame {"
        " border: 1px dashed #cbd5f5;"
        " border-radius: 14px;"
        " background: #ffffff;"
        "}"
    ));
    event->acceptProposedAction();
}

MainWindow::MainWindow(QWidget *parent) : QMainWindow(parent), isRunning(false) {
    setupUi();
    controller = new CompressController(this);
    connect(controller, &CompressController::logMessage, this, &MainWindow::onLogMessage);
    connect(controller, &CompressController::progressChanged, this, &MainWindow::onProgressChanged);
    connect(controller, &CompressController::finished, this, &MainWindow::onFinished);
}

void MainWindow::setupUi() {
    setWindowTitle("Imgcompress Native");
    resize(980, 640);
    setStyleSheet(QStringLiteral(
        "QMainWindow { background: #f3f4f6; }"
        "QGroupBox {"
        " background: transparent;"
        " border: none;"
        " border-radius: 16px;"
        " margin-top: 18px;"
        "}"
        "QGroupBox#panel {"
        " background: #ffffff;"
        " border: 1px solid #e5e7eb;"
        " border-radius: 16px;"
        " margin-top: 0px;"
        "}"
        "QGroupBox::title {"
        " subcontrol-origin: margin;"
        " left: 16px;"
        " padding: 0 6px;"
        " color: #6b7280;"
        " font-weight: 600;"
        " font-size: 12px;"
        "}"
        "QGroupBox#panel::title {"
        " padding: 0px;"
        " height: 0px;"
        "}"
        "QFrame#card, QPlainTextEdit#card {"
        " background: #ffffff;"
        " border: 1px solid #e5e7eb;"
        " border-radius: 16px;"
        "}"
        "QPlainTextEdit#card {"
        " padding: 10px;"
        "}"
        "QPlainTextEdit#log {"
        " background: #0b0f1a;"
        " color: #e5e7eb;"
        " border: 1px solid #0f172a;"
        " border-radius: 16px;"
        " padding: 12px;"
        "}"
        "QLineEdit, QComboBox, QSpinBox {"
        " background: #f9fafb;"
        " border: 1px solid #e5e7eb;"
        " border-radius: 10px;"
        " padding: 7px 10px;"
        " color: #111827;"
        "}"
        "QComboBox::drop-down {"
        " border: none;"
        "}"
        "QComboBox QAbstractItemView {"
        " background: #ffffff;"
        " selection-background-color: #2563eb;"
        " selection-color: #ffffff;"
        "}"
        "QComboBox QAbstractItemView::item {"
        " padding: 6px 10px;"
        " color: #111827;"
        "}"
        "QComboBox QAbstractItemView::item:selected {"
        " background: #2563eb;"
        " color: #ffffff;"
        "}"
        "QComboBox QAbstractItemView::item:hover {"
        " background: #eff6ff;"
        " color: #111827;"
        "}"
        "QScrollBar:vertical {"
        " width: 8px;"
        " background: transparent;"
        " margin: 4px 0 4px 0;"
        "}"
        "QScrollBar::handle:vertical {"
        " background: #c7d2fe;"
        " border-radius: 4px;"
        " min-height: 24px;"
        "}"
        "QScrollBar::handle:vertical:hover {"
        " background: #818cf8;"
        "}"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {"
        " height: 0;"
        "}"
        "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {"
        " background: transparent;"
        "}"
        "QPlainTextEdit {"
        " background: #0f172a;"
        " color: #e2e8f0;"
        " border: 1px solid #1f2937;"
        " border-radius: 14px;"
        " padding: 12px;"
        "}"
        "QPushButton {"
        " background: #2563eb;"
        " color: #ffffff;"
        " border: none;"
        " border-radius: 10px;"
        " padding: 9px 16px;"
        " font-weight: 600;"
        "}"
        "QPushButton:hover {"
        " background: #1d4ed8;"
        "}"
        "QPushButton:pressed {"
        " background: #1e40af;"
        "}"
        "QPushButton:disabled {"
        " background: #cbd5e1;"
        " color: #64748b;"
        "}"
        "QPushButton#secondary {"
        " background: #f1f5f9;"
        " color: #334155;"
        "}"
        "QPushButton#secondary:hover {"
        " background: #e2e8f0;"
        "}"
        "QSpinBox::up-button, QSpinBox::down-button {"
        " width: 16px;"
        " border-left: 1px solid #e5e7eb;"
        " background: #f3f4f6;"
        "}"
        "QSpinBox::up-button:hover, QSpinBox::down-button:hover {"
        " background: #e5e7eb;"
        "}"
        "QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {"
        " background: #d1d5db;"
        "}"
        "QSpinBox::up-arrow {"
        " image: url(:/qt-project.org/styles/commonstyle/images/up_arrow.png);"
        " width: 7px;"
        " height: 7px;"
        "}"
        "QSpinBox::down-arrow {"
        " image: url(:/qt-project.org/styles/commonstyle/images/down_arrow.png);"
        " width: 7px;"
        " height: 7px;"
        "}"
        "QProgressBar {"
        " border: 1px solid #e5e7eb;"
        " border-radius: 8px;"
        " height: 12px;"
        " background: #ffffff;"
        " text-align: center;"
        "}"
        "QProgressBar::chunk {"
        " background: #22c55e;"
        " border-radius: 8px;"
        "}"
    ));

    auto *central = new QWidget(this);
    auto *rootLayout = new QGridLayout();
    rootLayout->setContentsMargins(16, 16, 16, 16);
    rootLayout->setHorizontalSpacing(16);
    rootLayout->setVerticalSpacing(12);

    dropArea = new DropArea(this);
    dropArea->setObjectName("card");
    connect(dropArea, &DropArea::dropped, this, &MainWindow::onDropPaths);
    logArea = new QPlainTextEdit(this);
    logArea->setObjectName("log");
    logArea->setReadOnly(true);
    logArea->setPlaceholderText("压缩日志将在这里显示");
    logArea->setMinimumHeight(240);
    logSearchInput = new QLineEdit(this);
    logSearchInput->setPlaceholderText("搜索日志");
    logSearchInput->setMinimumHeight(30);
    connect(logSearchInput, &QLineEdit::textChanged, this, [this]() {
        updateLogSearchHighlights();
    });

    auto *pathGroup = new QGroupBox(this);
    pathGroup->setObjectName("panel");
    auto *pathLayout = new QGridLayout();
    pathLayout->setContentsMargins(8, 6, 8, 6);
    pathLayout->setHorizontalSpacing(8);
    pathLayout->setVerticalSpacing(6);
    auto *inputLayout = new QHBoxLayout();
    inputLine = new QLineEdit(this);
    inputLine->setMinimumHeight(30);
    inputLine->setPlaceholderText("请选择输入目录或拖拽文件");
    connect(inputLine, &QLineEdit::textEdited, this, [this](const QString &text) {
        if (!text.trimmed().isEmpty() && !selectedFiles.isEmpty()) {
            setSelectedFiles(QStringList());
        }
        updateSelectionMode();
    });
    auto *inputButton = new QPushButton("选择输入目录", this);
    inputButton->setFixedWidth(130);
    inputButton->setObjectName("secondary");
    connect(inputButton, &QPushButton::clicked, this, &MainWindow::pickInputDir);
    inputLayout->addWidget(inputLine);
    inputLayout->addWidget(inputButton);
    auto *inputLabel = new QLabel("目录", this);
    inputLabel->setAlignment(Qt::AlignLeft | Qt::AlignVCenter);
    pathLayout->addWidget(inputLabel, 0, 0);
    pathLayout->addLayout(inputLayout, 0, 1);

    auto *outputLayout = new QHBoxLayout();
    outputLine = new QLineEdit(this);
    outputLine->setMinimumHeight(30);
    outputLine->setPlaceholderText("默认为输入目录，可单独选择");
    auto *outputButton = new QPushButton("选择输出目录", this);
    outputButton->setFixedWidth(130);
    outputButton->setObjectName("secondary");
    connect(outputButton, &QPushButton::clicked, this, &MainWindow::pickOutputDir);
    outputLayout->addWidget(outputLine);
    outputLayout->addWidget(outputButton);
    auto *outputLabel = new QLabel("输出", this);
    outputLabel->setAlignment(Qt::AlignLeft | Qt::AlignVCenter);
    pathLayout->addWidget(outputLabel, 2, 0);
    pathLayout->addLayout(outputLayout, 2, 1);

    auto *filesLayout = new QHBoxLayout();
    filesLine = new QLineEdit(this);
    filesLine->setReadOnly(true);
    filesLine->setMinimumHeight(30);
    filesLine->setPlaceholderText("未选择");
    filesButton = new QPushButton("选择文件", this);
    filesButton->setFixedWidth(130);
    filesButton->setObjectName("secondary");
    connect(filesButton, &QPushButton::clicked, this, &MainWindow::pickFiles);
    filesLayout->addWidget(filesLine);
    filesLayout->addWidget(filesButton);
    auto *filesLabel = new QLabel("文件", this);
    filesLabel->setAlignment(Qt::AlignLeft | Qt::AlignVCenter);
    pathLayout->addWidget(filesLabel, 1, 0);
    pathLayout->addLayout(filesLayout, 1, 1);
    pathLayout->setColumnStretch(1, 1);
    pathGroup->setLayout(pathLayout);
    pathGroup->setMaximumHeight(190);
    pathGroup->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);

    auto *optionsGroup = new QGroupBox(this);
    optionsGroup->setObjectName("panel");
    auto *optionsGroupLayout = new QVBoxLayout();
    optionsGroupLayout->setSpacing(12);
    auto *optionsLayout = new QFormLayout();
    optionsLayout->setSpacing(10);
    optionsLayout->setLabelAlignment(Qt::AlignLeft | Qt::AlignVCenter);
    optionsLayout->setFieldGrowthPolicy(QFormLayout::ExpandingFieldsGrow);
    losslessCheck = new QCheckBox("无损压缩", this);
    profileCombo = new QComboBox(this);
    profileCombo->addItems({"高质量(推荐)", "均衡", "强压缩"});
    profileCombo->setCurrentIndex(2);
    profileCombo->setMaxVisibleItems(8);
    profileCombo->setView(new QListView(profileCombo));
    profileCombo->view()->setVerticalScrollMode(QAbstractItemView::ScrollPerPixel);
    qualitySlider = new QSlider(Qt::Horizontal, this);
    qualitySlider->setRange(10, 100);
    qualitySlider->setValue(85);
    qualityValue = new QLabel("85", this);
    qualityValue->setFixedWidth(36);
    qualityValue->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
    connect(qualitySlider, &QSlider::valueChanged, this, [this](int value) {
        qualityValue->setText(QString::number(value));
    });
    auto *qualityLayout = new QHBoxLayout();
    qualityLayout->addWidget(qualitySlider);
    qualityLayout->addWidget(qualityValue);
    optionsLayout->addRow(losslessCheck);
    optionsLayout->addRow("压缩预设", profileCombo);
    optionsLayout->addRow("有损质量", qualityLayout);
    concurrencySpin = new QSpinBox(this);
    int idealThreads = QThread::idealThreadCount();
    if (idealThreads < 1) {
        idealThreads = 4;
    }
    const int maxThreads = qMax(1, idealThreads - 1);
    concurrencySpin->setRange(1, maxThreads);
    concurrencySpin->setValue(maxThreads);
    concurrencySpin->setFixedWidth(88);
    optionsLayout->addRow(QString("并发数(≤%1)").arg(maxThreads), concurrencySpin);

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
    optionsLayout->addRow("输入格式", formatLayout);

    outputFormatCombo = new QComboBox(this);
    outputFormatCombo->addItem("保持原格式", "original");
    outputFormatCombo->addItem("JPG", "jpg");
    outputFormatCombo->addItem("PNG", "png");
    outputFormatCombo->addItem("WebP", "webp");
    outputFormatCombo->addItem("GIF", "gif");
    outputFormatCombo->setMaxVisibleItems(8);
    outputFormatCombo->setView(new QListView(outputFormatCombo));
    outputFormatCombo->view()->setVerticalScrollMode(QAbstractItemView::ScrollPerPixel);
    optionsLayout->addRow("输出格式", outputFormatCombo);

    auto *resizeLayout = new QHBoxLayout();
    resizeModeCombo = new QComboBox(this);
    resizeModeCombo->addItem("原尺寸", 0);
    resizeModeCombo->addItem("宽高等比", 1);
    resizeModeCombo->addItem("强制裁剪", 2);
    resizeModeCombo->setCurrentIndex(0);
    resizeModeCombo->setMaxVisibleItems(8);
    resizeModeCombo->setView(new QListView(resizeModeCombo));
    resizeModeCombo->view()->setVerticalScrollMode(QAbstractItemView::ScrollPerPixel);
    widthInput = new QLineEdit(this);
    heightInput = new QLineEdit(this);
    sizeValidator = new QIntValidator(16, 8192, this);
    widthInput->setValidator(sizeValidator);
    heightInput->setValidator(sizeValidator);
    widthInput->setFixedWidth(72);
    heightInput->setFixedWidth(72);
    widthInput->setAlignment(Qt::AlignCenter);
    heightInput->setAlignment(Qt::AlignCenter);
    widthInput->setPlaceholderText("宽");
    heightInput->setPlaceholderText("高");
    widthInput->setEnabled(false);
    heightInput->setEnabled(false);
    connect(resizeModeCombo, QOverload<int>::of(&QComboBox::currentIndexChanged), this, [this]() {
        updateCompressionOptionsState();
    });
    sizeLabel = new QLabel("×", this);
    sizeLabel->setAlignment(Qt::AlignCenter);
    sizeLabel->setFixedWidth(12);
    resizeLayout->addWidget(resizeModeCombo);
    resizeLayout->addWidget(widthInput);
    resizeLayout->addWidget(sizeLabel);
    resizeLayout->addWidget(heightInput);
    resizeLayout->addStretch();
    optionsLayout->addRow("输出尺寸", resizeLayout);
    optionsGroupLayout->addLayout(optionsLayout);

    progressBar = new QProgressBar(this);
    progressBar->setValue(0);

    startButton = new QPushButton("开始压缩", this);
    startButton->setMinimumHeight(44);
    startButton->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    connect(startButton, &QPushButton::clicked, this, &MainWindow::startCompression);

    connect(losslessCheck, &QCheckBox::toggled, this, [this]() {
        updateCompressionOptionsState();
    });

    auto *actionLayout = new QHBoxLayout();
    actionLayout->setSpacing(10);
    actionLayout->addWidget(progressBar, 1);
    actionLayout->addWidget(startButton);
    optionsGroupLayout->addLayout(actionLayout);
    optionsGroup->setLayout(optionsGroupLayout);
    optionsGroup->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);

    auto *pathContainer = new QWidget(this);
    auto *pathContainerLayout = new QVBoxLayout(pathContainer);
    pathContainerLayout->setContentsMargins(0, 16, 0, 0);
    pathContainerLayout->setSpacing(0);
    pathContainerLayout->addWidget(pathGroup);

    pathGroup->setMinimumWidth(360);
    pathGroup->setMaximumWidth(440);
    optionsGroup->setMinimumWidth(360);
    optionsGroup->setMaximumWidth(440);

    auto *logContainer = new QWidget(this);
    auto *logLayout = new QVBoxLayout(logContainer);
    logLayout->setContentsMargins(0, 0, 0, 0);
    logLayout->setSpacing(8);
    logLayout->addWidget(logSearchInput);
    logLayout->addWidget(logArea, 1);

    rootLayout->addWidget(dropArea, 0, 0);
    rootLayout->addWidget(logContainer, 1, 0);
    rootLayout->addWidget(pathContainer, 0, 1);
    rootLayout->addWidget(optionsGroup, 1, 1);
    rootLayout->setColumnStretch(0, 3);
    rootLayout->setColumnStretch(1, 2);
    rootLayout->setRowStretch(0, 2);
    rootLayout->setRowStretch(1, 3);

    central->setLayout(rootLayout);
    setCentralWidget(central);
    updateCompressionOptionsState();
}

void MainWindow::pickInputDir() {
    clearSelectedFiles();
    const QString dir = openDirectoryDialog("选择输入目录", inputLine->text());
    if (!dir.isEmpty()) {
        inputLine->setText(dir);
    }
    updateSelectionMode();
}

void MainWindow::pickOutputDir() {
    QString initialDir = outputLine->text();
    if (initialDir.trimmed().isEmpty()) {
        initialDir = inputLine->text();
    }
    const QString dir = openDirectoryDialog("选择输出目录", initialDir);
    if (!dir.isEmpty()) {
        outputLine->setText(dir);
    }
}

void MainWindow::pickFiles() {
    const QStringList files = openFilesDialog("选择图片文件");
    if (!files.isEmpty()) {
        setSelectedFiles(files);
    }
    updateSelectionMode();
}

void MainWindow::clearSelectedFiles() {
    setSelectedFiles(QStringList());
    updateSelectionMode();
}

void MainWindow::startCompression() {
    if (!startButton->isEnabled() || isRunning) {
        return;
    }
    const QStringList formats = selectedInputFormats();
    if (formats.isEmpty()) {
        onLogMessage("请选择至少一种格式");
        return;
    }
    if (!selectedFiles.isEmpty()) {
        const QString baseDir = commonBaseDir(selectedFiles);
        QString outputDir = outputLine->text().trimmed();
        if (baseDir.isEmpty() || !QDir(baseDir).exists()) {
            onLogMessage("请输入有效的输入目录");
            return;
        }
        if (outputDir.isEmpty()) {
            outputDir = baseDir;
        }
        logArea->clear();
        updateLogSearchHighlights();
        if (!startFilesCompression(selectedFiles, baseDir, outputDir, formats)) {
            return;
        }
    } else {
        const QString inputDir = inputLine->text().trimmed();
        QString outputDir = outputLine->text().trimmed();
        if (inputDir.isEmpty()) {
            onLogMessage("请选择输入目录或选择文件");
            return;
        }
        if (!QDir(inputDir).exists()) {
            onLogMessage("请输入有效的输入目录");
            return;
        }
        if (outputDir.isEmpty()) {
            outputDir = inputDir;
        }
        logArea->clear();
        updateLogSearchHighlights();
        if (!startDirCompression(inputDir, outputDir, formats)) {
            return;
        }
    }
    isRunning = true;
    startButton->setEnabled(false);
    progressBar->setValue(0);
}

void MainWindow::onLogMessage(const QString &message) {
    QTextCharFormat format;
    if (message.contains("实际格式为") && message.contains("不一致")) {
        format.setForeground(QColor("#f59e0b"));
    } else {
        format.setForeground(message.contains("失败") ? QColor("#ef4444") : QColor("#e5e7eb"));
    }
    QTextCursor cursor = logArea->textCursor();
    cursor.movePosition(QTextCursor::End);
    cursor.insertText(message + "\n", format);
    logArea->setTextCursor(cursor);
    logArea->ensureCursorVisible();
    updateLogSearchHighlights();
}

void MainWindow::onProgressChanged(int percent) {
    progressBar->setValue(percent);
}

void MainWindow::onFinished() {
    progressBar->setValue(100);
    isRunning = false;
    startButton->setEnabled(true);
    updateSelectionMode();
}

void MainWindow::onDropPaths(const QStringList &paths) {
    if (!startButton->isEnabled()) {
        return;
    }
    if (paths.isEmpty()) {
        return;
    }
    const QStringList files = collectFilesFromPaths(paths);
    if (!files.isEmpty()) {
        outputLine->clear();
        inputLine->clear();
        setSelectedFiles(files);
        QStringList formats = selectedInputFormats();
        if (formats.isEmpty()) {
            formats = defaultInputFormats();
        }
        const QString baseDir = commonBaseDir(files);
        logArea->clear();
        updateLogSearchHighlights();
        if (startFilesCompression(files, baseDir, baseDir, formats)) {
            isRunning = true;
            startButton->setEnabled(false);
            progressBar->setValue(0);
        }
        return;
    }
    if (paths.size() == 1) {
        const QFileInfo info(paths.first());
        if (info.exists() && info.isDir()) {
            clearSelectedFiles();
            inputLine->setText(info.absoluteFilePath());
            updateSelectionMode();
            return;
        }
    }
    onLogMessage("未找到可压缩图片");
}

void MainWindow::updateLogSearchHighlights() {
    const QString keyword = logSearchInput->text().trimmed();
    QList<QTextEdit::ExtraSelection> selections;
    if (!keyword.isEmpty()) {
        QTextCursor cursor(logArea->document());
        QTextCharFormat format;
        format.setBackground(QColor("#f59e0b"));
        format.setForeground(QColor("#0b0f1a"));
        while (true) {
            cursor = logArea->document()->find(keyword, cursor);
            if (cursor.isNull()) {
                break;
            }
            QTextEdit::ExtraSelection selection;
            selection.cursor = cursor;
            selection.format = format;
            selections.append(selection);
        }
    }
    logArea->setExtraSelections(selections);
}

void MainWindow::updateSelectionMode() {
    const bool hasFiles = !selectedFiles.isEmpty();
    inputLine->setEnabled(!hasFiles);
    if (!isRunning) {
        const bool hasInput = !inputLine->text().trimmed().isEmpty();
        startButton->setEnabled(hasFiles || hasInput);
    }
}

void MainWindow::setSelectedFiles(const QStringList &files) {
    selectedFiles = files;
    updateFileSummary();
    if (!selectedFiles.isEmpty()) {
        inputLine->clear();
    }
    updateSelectionMode();
}

void MainWindow::updateFileSummary() {
    if (selectedFiles.isEmpty()) {
        filesLine->setText("未选择文件");
        return;
    }
    filesLine->setText(QString("已选择 %1 张图片").arg(selectedFiles.size()));
}

QStringList MainWindow::collectFilesFromPaths(const QStringList &paths) const {
    const QStringList filters = {"*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp"};
    QSet<QString> found;
    for (const QString &path : paths) {
        QFileInfo info(path);
        if (!info.exists()) {
            continue;
        }
        if (info.isFile()) {
            const QString suffix = info.suffix().toLower();
            if (suffix == "jpg" || suffix == "jpeg" || suffix == "png" || suffix == "gif" || suffix == "webp") {
                found.insert(info.absoluteFilePath());
            }
            continue;
        }
        if (info.isDir()) {
            QDirIterator it(info.absoluteFilePath(), filters, QDir::Files, QDirIterator::Subdirectories);
            while (it.hasNext()) {
                found.insert(it.next());
            }
        }
    }
    return QStringList(found.begin(), found.end());
}

QString MainWindow::commonBaseDir(const QStringList &files) const {
    if (files.isEmpty()) {
        return QString();
    }
    const QString firstPath = QDir::fromNativeSeparators(QFileInfo(files.first()).absolutePath());
    QStringList parts = firstPath.split('/', Qt::SkipEmptyParts);
    QString prefix;
    const bool isDrive = firstPath.contains(":/");
    const bool isUNC = firstPath.startsWith("//");
    if (isDrive) {
        if (!parts.isEmpty()) {
            prefix = parts.takeFirst() + ":/";
        }
    } else if (isUNC) {
        prefix = "//";
    } else if (firstPath.startsWith("/")) {
        prefix = "/";
    }
    int commonCount = parts.size();
    for (const QString &file : files) {
        const QString path = QDir::fromNativeSeparators(QFileInfo(file).absolutePath());
        QStringList current = path.split('/', Qt::SkipEmptyParts);
        if (isDrive && !current.isEmpty()) {
            current.takeFirst();
        }
        commonCount = std::min(commonCount, static_cast<int>(current.size()));
        for (int i = 0; i < commonCount; ++i) {
            if (parts[i] != current[i]) {
                commonCount = i;
                break;
            }
        }
    }
    const QString base = (!prefix.isEmpty() ? prefix + parts.mid(0, commonCount).join("/") : parts.mid(0, commonCount).join("/"));
    if (base.isEmpty() || !QDir(base).exists()) {
        return QFileInfo(files.first()).absolutePath();
    }
    return base;
}

QString MainWindow::selectedOutputFormat() const {
    const QVariant value = outputFormatCombo->currentData();
    if (value.isValid()) {
        return value.toString();
    }
    return "original";
}

QString MainWindow::openDirectoryDialog(const QString &title, const QString &initialDir) {
    QString startDir = initialDir.trimmed();
    if (startDir.isEmpty()) {
        startDir = QDir::homePath();
    }
    return QFileDialog::getExistingDirectory(this, title, startDir, QFileDialog::ShowDirsOnly);
}

QStringList MainWindow::openFilesDialog(const QString &title) {
    return QFileDialog::getOpenFileNames(
        this,
        title,
        QDir::homePath(),
        "Images (*.jpg *.jpeg *.png *.gif *.webp)"
    );
}

QStringList MainWindow::selectedInputFormats() const {
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
    return formats;
}

QStringList MainWindow::defaultInputFormats() const {
    return {"jpg", "jpeg", "png", "gif", "webp"};
}

bool MainWindow::startDirCompression(
    const QString &inputDir,
    const QString &outputDir,
    const QStringList &formats
) {
    if (outputDir.trimmed().isEmpty()) {
        onLogMessage("请输入有效的输出目录");
        return false;
    }
    QDir outputRoot(outputDir);
    if (!outputRoot.exists() && !outputRoot.mkpath(".")) {
        onLogMessage("请输入有效的输出目录");
        return false;
    }
    const QString outputFormat = selectedOutputFormat();
    const int resizeMode = resizeModeCombo->currentData().toInt();
    const bool resizeEnabled = resizeMode != 0;
    int targetWidth = 0;
    int targetHeight = 0;
    if (resizeEnabled && !readResizeSize(targetWidth, targetHeight)) {
        return false;
    }
    controller->start(
        inputDir,
        outputDir,
        formats,
        losslessCheck->isChecked(),
        qualitySlider->value(),
        profileCombo->currentText(),
        outputFormat,
        concurrencySpin->value(),
        resizeEnabled,
        targetWidth,
        targetHeight,
        resizeMode
    );
    return true;
}

bool MainWindow::startFilesCompression(
    const QStringList &files,
    const QString &baseDir,
    const QString &outputDir,
    const QStringList &formats
) {
    if (baseDir.isEmpty() || !QDir(baseDir).exists()) {
        onLogMessage("请输入有效的输入目录");
        return false;
    }
    if (files.isEmpty()) {
        onLogMessage("未找到可压缩图片");
        return false;
    }
    if (outputDir.trimmed().isEmpty()) {
        onLogMessage("请输入有效的输出目录");
        return false;
    }
    QDir outputRoot(outputDir);
    if (!outputRoot.exists() && !outputRoot.mkpath(".")) {
        onLogMessage("请输入有效的输出目录");
        return false;
    }
    const QString outputFormat = selectedOutputFormat();
    const int resizeMode = resizeModeCombo->currentData().toInt();
    const bool resizeEnabled = resizeMode != 0;
    int targetWidth = 0;
    int targetHeight = 0;
    if (resizeEnabled && !readResizeSize(targetWidth, targetHeight)) {
        return false;
    }
    controller->startFiles(
        files,
        baseDir,
        outputDir,
        formats,
        losslessCheck->isChecked(),
        qualitySlider->value(),
        profileCombo->currentText(),
        outputFormat,
        concurrencySpin->value(),
        resizeEnabled,
        targetWidth,
        targetHeight,
        resizeMode
    );
    return true;
}

void MainWindow::updateCompressionOptionsState() {
    const bool lossless = losslessCheck->isChecked();
    formatJpg->setEnabled(!lossless);
    formatPng->setEnabled(!lossless);
    formatGif->setEnabled(!lossless);
    formatWebp->setEnabled(!lossless);
    profileCombo->setEnabled(!lossless);
    qualitySlider->setEnabled(!lossless);
    qualityValue->setEnabled(!lossless);
    outputFormatCombo->setEnabled(!lossless);
    if (lossless) {
        widthInput->setEnabled(false);
        heightInput->setEnabled(false);
        widthInput->setVisible(false);
        heightInput->setVisible(false);
        sizeLabel->setVisible(false);
        resizeModeCombo->setEnabled(false);
    } else {
        const int resizeMode = resizeModeCombo->currentData().toInt();
        const bool resizeEnabled = resizeMode != 0;
        widthInput->setEnabled(resizeEnabled);
        heightInput->setEnabled(resizeEnabled);
        widthInput->setVisible(resizeEnabled);
        heightInput->setVisible(resizeEnabled);
        sizeLabel->setVisible(resizeEnabled);
        resizeModeCombo->setEnabled(true);
        if (!resizeEnabled) {
            widthInput->clear();
            heightInput->clear();
        }
    }
}

bool MainWindow::readResizeSize(int &width, int &height) {
    bool okWidth = false;
    bool okHeight = false;
    const int parsedWidth = widthInput->text().trimmed().toInt(&okWidth);
    const int parsedHeight = heightInput->text().trimmed().toInt(&okHeight);
    if (!okWidth || !okHeight || parsedWidth <= 0 || parsedHeight <= 0) {
        onLogMessage("请输入有效的输出尺寸");
        return false;
    }
    width = parsedWidth;
    height = parsedHeight;
    return true;
}
