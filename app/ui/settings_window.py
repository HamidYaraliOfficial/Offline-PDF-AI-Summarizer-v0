from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QVBoxLayout, QWidget)
from app.utils.hardware import hardware_report
from app.ai.model_manager import find_gguf_models, models_directory


class SettingsWindow(QDialog):
    def __init__(self, config: dict, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(640)
        self._config = dict(config)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        configured_model = str(config.get("model_path", ""))
        if not configured_model:
            available_models = find_gguf_models()
            if len(available_models) == 1:
                configured_model = str(available_models[0])
        self.model_path = QLineEdit(configured_model)
        model_row = QHBoxLayout()
        model_row.addWidget(self.model_path, 1)
        browse_model = QPushButton("Browse GGUF…")
        browse_model.clicked.connect(self._browse_model)
        model_row.addWidget(browse_model)
        model_wrap = QWidget(); model_wrap.setLayout(model_row)
        form.addRow("AI model (.gguf)", model_wrap)

        self.cpu_threads = QSpinBox(); self.cpu_threads.setRange(1, max(1, int(hardware_report().get("CPU threads", 1)))); self.cpu_threads.setValue(int(config.get("cpu_threads", 4)))
        form.addRow("CPU threads", self.cpu_threads)
        self.context_size = QComboBox()
        for v in (2048, 4096, 8192, 16384, 32768): self.context_size.addItem(str(v), v)
        idx = self.context_size.findData(int(config.get("context_size", 4096))); self.context_size.setCurrentIndex(max(0, idx))
        form.addRow("Context size", self.context_size)
        self.gpu_layers = QSpinBox(); self.gpu_layers.setRange(-1, 200); self.gpu_layers.setValue(int(config.get("gpu_layers", 0)))
        self.gpu_layers.setToolTip("0 = CPU only; -1 = try to offload all layers to a supported GPU backend.")
        form.addRow("GPU layers (0 = CPU)", self.gpu_layers)
        self.enable_ocr = QCheckBox("Use local Tesseract OCR for pages with little or no text")
        self.enable_ocr.setChecked(bool(config.get("enable_ocr", False)))
        form.addRow("OCR", self.enable_ocr)
        self.tesseract_path = QLineEdit(str(config.get("tesseract_path", "")))
        ocr_row = QHBoxLayout(); ocr_row.addWidget(self.tesseract_path, 1)
        browse_tesseract = QPushButton("Browse…"); browse_tesseract.clicked.connect(self._browse_tesseract); ocr_row.addWidget(browse_tesseract)
        ocr_wrap = QWidget(); ocr_wrap.setLayout(ocr_row)
        form.addRow("Tesseract executable", ocr_wrap)
        self.ocr_languages = QLineEdit(str(config.get("ocr_languages", "fas+eng")))
        self.ocr_languages.setToolTip("Tesseract language codes joined with +, e.g. fas+eng. Install the same language data locally.")
        form.addRow("OCR languages", self.ocr_languages)
        self.output_dir = QLineEdit(str(config.get("output_directory", "")))
        out_row = QHBoxLayout(); out_row.addWidget(self.output_dir, 1)
        browse_out = QPushButton("Browse…"); browse_out.clicked.connect(self._browse_output); out_row.addWidget(browse_out)
        out_wrap = QWidget(); out_wrap.setLayout(out_row)
        form.addRow("Output directory", out_wrap)
        self.theme = QComboBox(); self.theme.addItems(["System", "Light", "Dark"]); self.theme.setCurrentText(str(config.get("theme", "System")))
        form.addRow("Theme", self.theme)
        layout.addLayout(form)
        machine = hardware_report()
        hardware_text = "Detected hardware:\n" + "\n".join(f"{k}: {v}" for k, v in machine.items())
        info = QLabel(hardware_text); info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse); info.setWordWrap(True)
        layout.addWidget(info)
        layout.addWidget(QLabel("Privacy: model inference, PDF extraction, OCR, settings and history run locally. The app does not require an API key."))
        buttons = QHBoxLayout(); buttons.addStretch(1)
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject)
        save = QPushButton("Save settings"); save.setDefault(True); save.clicked.connect(self.accept)
        buttons.addWidget(cancel); buttons.addWidget(save); layout.addLayout(buttons)

    def _browse_model(self) -> None:
        initial_dir = Path(self.model_path.text()).parent if self.model_path.text() else models_directory()
        path, _ = QFileDialog.getOpenFileName(self, "Select local GGUF model", str(initial_dir), "GGUF models (*.gguf)")
        if path: self.model_path.setText(path)

    def _browse_tesseract(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Tesseract executable", "", "Executable (tesseract.exe);;All files (*)")
        if path: self.tesseract_path.setText(path)

    def _browse_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choose output folder", self.output_dir.text() or str(Path.home()))
        if path: self.output_dir.setText(path)

    def values(self) -> dict:
        return {
            "model_path": self.model_path.text().strip(),
            "cpu_threads": self.cpu_threads.value(),
            "context_size": int(self.context_size.currentData()),
            "gpu_layers": self.gpu_layers.value(),
            "enable_ocr": self.enable_ocr.isChecked(),
            "tesseract_path": self.tesseract_path.text().strip(),
            "ocr_languages": self.ocr_languages.text().strip() or "eng",
            "output_directory": self.output_dir.text().strip() or str(Path.home() / "Documents" / "PDF Summaries"),
            "theme": self.theme.currentText(),
        }
