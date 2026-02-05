from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal, QSettings
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QCheckBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QSlider,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QFrame,
)

from .compress import compress_file, get_engine_status
from .models import CompressOptions, CompressResult, iter_image_files


class CompressWorker(QObject):
    progress = Signal(int, str, CompressResult)
    finished = Signal(list)

    def __init__(self, files: list[Path], options: CompressOptions) -> None:
        super().__init__()
        self.files = files
        self.options = options

    def run(self) -> None:
        results = []
        total = len(self.files)
        for index, path in enumerate(self.files, start=1):
            result = compress_file(path, self.options)
            results.append(result)
            percent = int(index * 100 / total)
            self.progress.emit(percent, path.name, result)
        self.finished.emit(results)


class DropArea(QFrame):
    dropped = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setMinimumHeight(110)
        self.setStyleSheet(
            "QFrame { border: 1px solid #d0d0d0; border-radius: 8px; background: #fafafa; }"
        )
        layout = QVBoxLayout()
        label = QLabel("拖拽图片/文件夹到此处立即压缩（输出同目录）")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        paths = [Path(url.toLocalFile()) for url in urls if url.toLocalFile()]
        if paths:
            self.dropped.emit(paths)


class MainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Imgcompress")
        self.resize(900, 600)
        self.thread: QThread | None = None
        self.worker: CompressWorker | None = None
        self.settings = QSettings("Imgcompress", "Imgcompress")
        self.selected_files: list[Path] = []
        self.output_mode = "mirror"
        self.drop_area = DropArea()
        self.input_line = QLineEdit()
        self.output_line = QLineEdit()
        self.files_line = QLineEdit()
        self.lossless_checkbox = QCheckBox("无损压缩")
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_value = QLabel()
        self.profile_combo = QComboBox()
        self.format_jpg = QCheckBox("JPG")
        self.format_png = QCheckBox("PNG")
        self.format_gif = QCheckBox("GIF")
        self.format_webp = QCheckBox("WebP")
        self.start_button = QPushButton("开始压缩")
        self.progress_bar = QProgressBar()
        self.log_area = QPlainTextEdit()
        self.setup_ui()

    def setup_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.drop_area)
        layout.addWidget(self.build_path_group())
        layout.addWidget(self.build_options_group())
        layout.addWidget(self.build_action_group())
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_area)
        central.setLayout(layout)
        self.setCentralWidget(central)
        self.log_area.setReadOnly(True)
        self.files_line.setReadOnly(True)
        self.progress_bar.setValue(0)
        self.load_settings()
        self.lossless_checkbox.setChecked(False)
        self.quality_slider.setRange(10, 100)
        self.quality_slider.setValue(85)
        self.quality_value.setText("85")
        self.quality_slider.setEnabled(True)
        self.profile_combo.addItems(["高质量(推荐)", "均衡", "强压缩"])
        self.format_jpg.setChecked(True)
        self.format_png.setChecked(True)
        self.format_gif.setChecked(True)
        self.format_webp.setChecked(True)
        self.lossless_checkbox.toggled.connect(self.on_lossless_toggled)
        self.quality_slider.valueChanged.connect(self.on_quality_changed)
        self.profile_combo.currentIndexChanged.connect(self.on_profile_changed)
        self.start_button.clicked.connect(self.on_start)
        self.drop_area.dropped.connect(self.on_drop_paths)
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        self.menuBar().addAction(exit_action)

    def build_path_group(self) -> QGroupBox:
        group = QGroupBox("路径")
        layout = QGridLayout()
        input_button = QPushButton("选择输入目录")
        file_button = QPushButton("选择图片文件")
        output_button = QPushButton("选择输出目录")
        input_button.clicked.connect(self.pick_input_dir)
        file_button.clicked.connect(self.pick_input_files)
        output_button.clicked.connect(self.pick_output_dir)
        layout.addWidget(QLabel("输入目录"), 0, 0)
        layout.addWidget(self.input_line, 0, 1)
        layout.addWidget(input_button, 0, 2)
        layout.addWidget(QLabel("图片文件"), 1, 0)
        layout.addWidget(self.files_line, 1, 1)
        layout.addWidget(file_button, 1, 2)
        layout.addWidget(QLabel("输出目录"), 2, 0)
        layout.addWidget(self.output_line, 2, 1)
        layout.addWidget(output_button, 2, 2)
        group.setLayout(layout)
        return group

    def build_options_group(self) -> QGroupBox:
        group = QGroupBox("压缩选项")
        layout = QFormLayout()
        format_layout = QHBoxLayout()
        format_layout.addWidget(self.format_jpg)
        format_layout.addWidget(self.format_png)
        format_layout.addWidget(self.format_gif)
        format_layout.addWidget(self.format_webp)
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_value)
        layout.addRow(self.lossless_checkbox)
        layout.addRow("压缩预设", self.profile_combo)
        layout.addRow("有损质量", quality_layout)
        layout.addRow("格式", format_layout)
        group.setLayout(layout)
        return group

    def build_action_group(self) -> QWidget:
        group = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(self.start_button)
        group.setLayout(layout)
        return group

    def pick_input_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择输入目录")
        if path:
            self.input_line.setText(path)
            self.selected_files = []
            self.files_line.setText("")
            self.output_mode = "mirror"

    def pick_input_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片文件",
            "",
            "Images (*.jpg *.jpeg *.png *.gif *.webp)",
        )
        if files:
            self.selected_files = [Path(file) for file in files]
            self.files_line.setText(f"已选 {len(self.selected_files)} 个文件")
            self.input_line.setText("")
            self.output_mode = "mirror"

    def pick_output_dir(self) -> None:
        default_dir = self.output_line.text().strip() or self.settings.value("output_dir", "")
        path = QFileDialog.getExistingDirectory(self, "选择输出目录", default_dir)
        if path:
            self.output_line.setText(path)
            self.save_output_dir(path)
            self.output_mode = "mirror"

    def on_lossless_toggled(self, checked: bool) -> None:
        self.quality_slider.setEnabled(not checked)
        self.profile_combo.setEnabled(not checked)

    def on_quality_changed(self, value: int) -> None:
        self.quality_value.setText(str(value))

    def on_profile_changed(self) -> None:
        text = self.profile_combo.currentText()
        if "强压缩" in text:
            self.set_quality_value(70)
        elif "均衡" in text:
            self.set_quality_value(80)
        else:
            self.set_quality_value(85)

    def set_quality_value(self, value: int) -> None:
        self.quality_slider.setValue(value)
        self.quality_value.setText(str(value))

    def on_start(self) -> None:
        if self.thread is not None:
            return
        output_text = self.output_line.text().strip()
        output_dir = Path(output_text) if output_text else None
        formats = self.get_selected_formats()
        if self.output_mode != "same_dir":
            if output_dir is None:
                self.append_log("请输入有效的输出目录")
                return
            if not output_dir.exists() or not output_dir.is_dir():
                output_dir = self.ensure_output_dir(output_dir, None)
            if output_dir is None:
                self.append_log("请输入有效的输出目录")
                return
        if not formats:
            self.append_log("请选择至少一种格式")
            return
        files = self.get_target_files(formats)
        if not files:
            self.append_log("未找到可压缩图片")
            return
        input_dir = self.get_input_dir(files)
        if self.output_mode != "same_dir":
            output_dir = self.ensure_output_dir(output_dir, input_dir)
            if output_dir is None:
                self.append_log("请输入有效的输出目录")
                return
            self.output_line.setText(str(output_dir))
            self.save_output_dir(str(output_dir))
        else:
            output_dir = input_dir
        self.start_compression(files, input_dir, output_dir, formats, self.output_mode)

    def start_compression(
        self,
        files: list[Path],
        input_dir: Path,
        output_dir: Path,
        formats: set[str],
        output_mode: str,
    ) -> None:
        options = CompressOptions(
            input_dir=input_dir,
            output_dir=output_dir,
            lossless=self.lossless_checkbox.isChecked(),
            quality=self.quality_slider.value(),
            quality_profile=self.get_selected_profile(),
            output_mode=output_mode,
            formats=formats,
        )
        self.start_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_area.clear()
        self.append_log(self.format_engine_status(options.lossless))
        self.append_log(f"开始压缩 {len(files)} 张图片")
        self.thread = QThread()
        self.worker = CompressWorker(files, options)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.on_thread_finished)
        self.thread.start()

    def get_target_files(self, formats: set[str]) -> list[Path]:
        if self.selected_files:
            patterns = {f".{fmt.lower()}" for fmt in formats}
            return [
                path for path in self.selected_files if path.suffix.lower() in patterns
            ]
        input_text = self.input_line.text().strip()
        if not input_text:
            return []
        input_dir = Path(input_text)
        if not input_dir.exists() or not input_dir.is_dir():
            return []
        return iter_image_files(input_dir, formats)

    def get_input_dir(self, files: list[Path]) -> Path:
        common = os.path.commonpath([str(path) for path in files])
        common_path = Path(common)
        if common_path.exists() and common_path.is_file():
            return common_path.parent
        return common_path

    def get_selected_formats(self) -> set[str]:
        formats = set()
        if self.format_jpg.isChecked():
            formats.update({"jpg", "jpeg"})
        if self.format_png.isChecked():
            formats.add("png")
        if self.format_gif.isChecked():
            formats.add("gif")
        if self.format_webp.isChecked():
            formats.add("webp")
        return formats

    def get_selected_profile(self) -> str:
        text = self.profile_combo.currentText()
        if "强压缩" in text:
            return "strong"
        if "均衡" in text:
            return "balanced"
        return "high"

    def on_progress(self, percent: int, name: str, result: CompressResult) -> None:
        self.progress_bar.setValue(percent)
        if result.success:
            ratio = (
                1 - (result.compressed_size / result.original_size)
                if result.original_size
                else 0
            )
            self.append_log(f"{name} 压缩完成，节省 {ratio:.1%}")
        else:
            self.append_log(f"{name} 压缩失败：{result.message}")

    def on_finished(self, results: list[CompressResult]) -> None:
        success_count = sum(1 for result in results if result.success)
        total_before = sum(result.original_size for result in results if result.success)
        total_after = sum(result.compressed_size for result in results if result.success)
        saved = total_before - total_after if total_before else 0
        ratio = saved / total_before if total_before else 0
        self.append_log(f"完成：成功 {success_count} 张，节省 {ratio:.1%}")
        self.progress_bar.setValue(100)

    def on_thread_finished(self) -> None:
        self.start_button.setEnabled(True)
        self.thread = None
        self.worker = None

    def append_log(self, text: str) -> None:
        self.log_area.appendPlainText(text)

    def on_drop_paths(self, paths: list[Path]) -> None:
        if self.thread is not None:
            return
        supported = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        files: list[Path] = []
        for path in paths:
            if path.is_dir():
                for item in path.rglob("*"):
                    if item.is_file() and item.suffix.lower() in supported:
                        files.append(item)
            elif path.is_file() and path.suffix.lower() in supported:
                files.append(path)
        unique_files = list(dict.fromkeys(files))
        if not unique_files:
            self.append_log("未找到可压缩图片")
            return
        formats = self.get_selected_formats()
        if not formats:
            formats = {"jpg", "jpeg", "png", "gif", "webp"}
        self.selected_files = unique_files
        self.files_line.setText(f"拖拽已选 {len(unique_files)} 个文件")
        self.input_line.setText("")
        self.output_line.setText("")
        self.output_mode = "same_dir"
        input_dir = self.get_input_dir(unique_files)
        self.start_compression(unique_files, input_dir, input_dir, formats, "same_dir")

    def load_settings(self) -> None:
        output_dir = self.settings.value("output_dir", "")
        if output_dir:
            self.output_line.setText(output_dir)

    def save_output_dir(self, path: str) -> None:
        self.settings.setValue("output_dir", path)

    def ensure_output_dir(self, output_dir: Path, input_dir: Path | None) -> Path | None:
        if output_dir.exists() and not output_dir.is_dir():
            return None
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def format_engine_status(self, lossless: bool) -> str:
        status = get_engine_status(lossless)
        parts = [f"{key}={value}" for key, value in status.items()]
        mode = "无损" if lossless else "有损"
        return f"压缩引擎({mode})：{'，'.join(parts)}"


def main() -> None:
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
