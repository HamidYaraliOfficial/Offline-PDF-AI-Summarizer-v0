from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent, QFont
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QProgressBar, QPushButton, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget, QDialog, QDialogButtonBox)
from app import __version__
from app.ai.model_manager import model_status
from app.export.txt import save_txt
from app.export.markdown import save_markdown
from app.export.docx import save_docx
from app.export.pdf import save_pdf
from app.storage.database import HistoryDatabase
from app.utils.config import ConfigManager, project_root
from app.ui.settings_window import SettingsWindow
from app.ui.worker import SummaryWorker

logger = logging.getLogger(__name__)


class HistoryDialog(QDialog):
    def __init__(self, db: HistoryDatabase, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        self.selected_result = None
        self.setWindowTitle("Local Summary History")
        self.resize(720, 420)
        layout = QVBoxLayout(self)
        self.items = QListWidget()
        self._ids: list[int] = []
        for row in db.list_recent():
            created = row.get("created_at", "")[:19].replace("T", " ")
            item = QListWidgetItem(f"{row.get('title')}  —  {row.get('summary_type')}  —  {row.get('page_count')} pages  —  {created}")
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            self.items.addItem(item); self._ids.append(row["id"])
        layout.addWidget(self.items)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Open).clicked.connect(self._open_selected)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.items.itemDoubleClicked.connect(lambda _item: self._open_selected())

    def _open_selected(self) -> None:
        item = self.items.currentItem()
        if not item:
            QMessageBox.information(self, "History", "Select a history entry first."); return
        self.selected_result = self.db.get(int(item.data(Qt.ItemDataRole.UserRole)))
        if self.selected_result: self.accept()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Offline PDF AI Summarizer")
        self.setMinimumSize(920, 720)
        self.setAcceptDrops(True)
        self.config = ConfigManager()
        self.db = HistoryDatabase()
        self.current_pdf: str | None = None
        self.current_result: dict | None = None
        self.worker: SummaryWorker | None = None
        self._close_when_done = False
        self._build_ui()
        self._apply_theme()
        self._update_model_status()

    def _build_ui(self) -> None:
        central = QWidget(); self.setCentralWidget(central)
        root = QVBoxLayout(central); root.setContentsMargins(20, 16, 20, 14); root.setSpacing(12)
        heading = QHBoxLayout()
        title = QLabel("Offline PDF AI Summarizer"); title.setFont(QFont("Segoe UI", 19, QFont.Weight.Bold))
        subtitle = QLabel(f"Local-first document summaries · v{__version__}"); subtitle.setStyleSheet("color: #7f8b9c")
        top_left = QVBoxLayout(); top_left.addWidget(title); top_left.addWidget(subtitle)
        heading.addLayout(top_left); heading.addStretch(1)
        self.history_button = QPushButton("History"); self.history_button.clicked.connect(self._show_history); heading.addWidget(self.history_button)
        self.settings_button = QPushButton("Settings"); self.settings_button.clicked.connect(self._show_settings); heading.addWidget(self.settings_button)
        root.addLayout(heading)

        self.drop_area = QLabel("Drop a PDF file here\n\nOR\n")
        self.drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_area.setMinimumHeight(150)
        self.drop_area.setStyleSheet("QLabel { border: 2px dashed #62748a; border-radius: 14px; padding: 18px; font-size: 16px; }")
        root.addWidget(self.drop_area)
        select_row = QHBoxLayout()
        self.select_button = QPushButton("Select PDF…"); self.select_button.clicked.connect(self._select_pdf); select_row.addWidget(self.select_button)
        self.file_info = QLabel("No PDF selected"); self.file_info.setWordWrap(True); select_row.addWidget(self.file_info, 1)
        root.addLayout(select_row)

        options = QHBoxLayout()
        options.addWidget(QLabel("Summary type:"))
        self.summary_type = QComboBox()
        self.summary_type.addItem("Short", "short")
        self.summary_type.addItem("Standard", "standard")
        self.summary_type.addItem("Detailed", "detailed")
        self.summary_type.addItem("Chapter by chapter", "chapter")
        self.summary_type.setCurrentIndex(1); options.addWidget(self.summary_type)
        options.addSpacing(18); options.addWidget(QLabel("Output language:"))
        self.language = QComboBox()
        self.language.addItem("Auto-detect", "auto")
        self.language.addItem("Persian", "fa")
        self.language.addItem("English", "en")
        self.language.addItem("Chinese", "zh")
        options.addWidget(self.language); options.addStretch(1)
        self.summarize_button = QPushButton("SUMMARIZE")
        self.summarize_button.setMinimumHeight(38); self.summarize_button.clicked.connect(self._start_summary); options.addWidget(self.summarize_button)
        self.cancel_button = QPushButton("Cancel"); self.cancel_button.setEnabled(False); self.cancel_button.clicked.connect(self._cancel_summary); options.addWidget(self.cancel_button)
        root.addLayout(options)

        self.progress = QProgressBar(); self.progress.setRange(0, 100); self.progress.setValue(0); root.addWidget(self.progress)
        self.status = QLabel("Ready. For AI summarization, select a local GGUF model in Settings."); self.status.setWordWrap(True); root.addWidget(self.status)
        self.model_status_label = QLabel(); self.model_status_label.setWordWrap(True); root.addWidget(self.model_status_label)

        self.tabs = QTabWidget()
        self.views: dict[str, QTextEdit] = {}
        for key, label in [("summary", "Summary"), ("key_points", "Key Points"), ("important_concepts", "Important Concepts"), ("keywords", "Keywords"), ("chapters", "Chapter Summaries")]:
            view = QTextEdit(); view.setReadOnly(True); view.setPlaceholderText(f"{label} will appear here after processing.")
            self.views[key] = view; self.tabs.addTab(view, label)
        root.addWidget(self.tabs, 1)
        self.metadata = QLabel("Document details will appear here."); self.metadata.setStyleSheet("color: #7f8b9c"); root.addWidget(self.metadata)
        export_row = QHBoxLayout(); export_row.addWidget(QLabel("Export result:"))
        for label, kind in [("Copy Summary", "copy"), ("Save TXT", "txt"), ("Save Markdown", "md"), ("Save PDF", "pdf"), ("Save DOCX", "docx")]:
            button = QPushButton(label); button.clicked.connect(lambda checked=False, k=kind: self._export(k)); export_row.addWidget(button)
        export_row.addStretch(1); root.addLayout(export_row)
        footer = QLabel("Created by Hamid Yarali · Copyright © 2026 · All rights reserved")
        footer.setAlignment(Qt.AlignmentFlag.AlignRight)
        footer.setStyleSheet("color: #7f8b9c; font-size: 9pt")
        root.addWidget(footer)
        self.setStatusBar(self.statusBar())
        self.statusBar().showMessage("All document processing is local; no cloud API or API key is required.")

    def _apply_theme(self) -> None:
        theme = self.config.get("theme", "System")
        if theme == "Dark":
            self.setStyleSheet("QMainWindow,QDialog { background:#17202b; color:#e7edf5 } QWidget { color:#e7edf5 } QTextEdit,QLineEdit,QComboBox,QListWidget { background:#202b39; color:#e7edf5; border:1px solid #405168; border-radius:5px; padding:5px } QPushButton { padding:8px 12px; border:1px solid #52657c; border-radius:7px; background:#26384d } QPushButton:hover { background:#334a64 } QProgressBar { border:1px solid #52657c; border-radius:5px; text-align:center } QProgressBar::chunk { background:#28a3a1; border-radius:4px }")
        elif theme == "Light":
            self.setStyleSheet("QMainWindow,QDialog { background:#f6f8fb; color:#152235 } QTextEdit,QLineEdit,QComboBox,QListWidget { background:white; color:#152235; border:1px solid #cbd5e1; border-radius:5px; padding:5px } QPushButton { padding:8px 12px; border:1px solid #b8c5d6; border-radius:7px; background:#edf2f8 } QPushButton:hover { background:#e0eaf5 }")

    def _update_model_status(self) -> None:
        ready, message = model_status(self.config.get("model_path", ""))
        self.model_status_label.setText(("✓ " if ready else "⚠ ") + message)
        self.model_status_label.setStyleSheet("color:#168052" if ready else "color:#b7791f")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() and any(url.toLocalFile().lower().endswith(".pdf") for url in event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".pdf"):
                self._set_pdf(path); event.acceptProposedAction(); return
        QMessageBox.warning(self, "Invalid file", "Please drop a PDF file.")

    def _select_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", str(Path.home()), "PDF documents (*.pdf)")
        if path: self._set_pdf(path)

    def _set_pdf(self, path: str) -> None:
        try:
            from app.pdf.extractor import inspect_pdf
            info = inspect_pdf(path)
            self.current_pdf = info.path
            size_mb = info.file_size / (1024 * 1024)
            self.file_info.setText(f"Selected: {Path(path).name}\nPages: {info.page_count} · Size: {size_mb:.2f} MB · Title: {info.title}")
            self.drop_area.setText("PDF selected — drop another file to replace it")
            self.status.setText("Ready to summarize. Processing happens locally on this computer.")
        except Exception as exc:
            QMessageBox.warning(self, "Could not open PDF", str(exc))

    def _start_summary(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        if not self.current_pdf:
            QMessageBox.information(self, "Select a PDF", "Choose or drop a PDF before starting."); return
        cfg = dict(self.config.data)
        # Validate model presence before launching a worker, while letting the runtime give more detail if needed.
        ready, status = model_status(cfg.get("model_path", ""))
        if not ready:
            answer = QMessageBox.question(self, "Local AI model not configured", status + "\n\nOpen Settings now?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer == QMessageBox.StandardButton.Yes: self._show_settings()
            return
        self.progress.setValue(0); self.summarize_button.setEnabled(False); self.cancel_button.setEnabled(True)
        self.status.setText("Starting local model…")
        self.worker = SummaryWorker(self.current_pdf, self.summary_type.currentData(), self.language.currentData(), cfg)
        self.worker.progress.connect(self._on_progress)
        self.worker.succeeded.connect(self._on_success)
        self.worker.failed.connect(self._on_failure)
        self.worker.cancelled.connect(self._on_cancelled)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def _on_progress(self, percent: int, message: str) -> None:
        self.progress.setValue(percent); self.status.setText(message)

    def _on_success(self, result: dict) -> None:
        self.current_result = result
        self._render_result(result)
        try: self.db.add(result)
        except Exception: logger.exception("Could not save summary history")
        warnings = result.get("warnings", []) or []
        if warnings:
            self.status.setText("Summary complete with a processing note: " + warnings[0])
        else:
            self.status.setText("Summary complete. Export or copy the result using the buttons below.")

    def _render_result(self, result: dict) -> None:
        self.views["summary"].setPlainText(result.get("summary", ""))
        self.views["key_points"].setPlainText(result.get("key_points", ""))
        self.views["important_concepts"].setPlainText(result.get("important_concepts", ""))
        self.views["keywords"].setPlainText(result.get("keywords", ""))
        chapters = result.get("chapter_summaries", []) or []
        self.views["chapters"].setPlainText("\n\n".join(f"{c.get('title', 'Section')}\n{'-' * min(60, max(8, len(c.get('title', 'Section'))))}\n{c.get('summary', '')}" for c in chapters) or "Chapter summaries are available when Chapter by chapter mode is selected and headings can be detected.")
        note = " · Some pages may need OCR" if result.get("warnings") else ""
        self.metadata.setText(f"{result.get('title')} · {result.get('page_count')} pages · Language: {result.get('language')} · Processing: {result.get('processing_seconds')} seconds{note}")
        self.tabs.setCurrentIndex(0)

    def _on_failure(self, message: str) -> None:
        self.status.setText("Summarization failed. See the message for possible fixes.")
        QMessageBox.critical(self, "Summarization failed", message)

    def _on_cancelled(self) -> None:
        self.status.setText("Processing cancelled. Temporary intermediate files were cleaned up.")

    def _on_worker_finished(self) -> None:
        self.summarize_button.setEnabled(True); self.cancel_button.setEnabled(False)
        self.worker = None
        if self._close_when_done:
            self.close()

    def _cancel_summary(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.cancel_button.setEnabled(False)
            self.status.setText("Cancellation requested. The active model call will finish before stopping.")

    def _show_settings(self) -> None:
        dialog = SettingsWindow(self.config.data, self)
        if dialog.exec():
            self.config.save(dialog.values())
            self._apply_theme(); self._update_model_status()
            self.status.setText("Settings saved locally.")

    def _show_history(self) -> None:
        dialog = HistoryDialog(self.db, self)
        if dialog.exec() and dialog.selected_result:
            self.current_result = dialog.selected_result
            self.current_pdf = self.current_result.get("source_path") or self.current_pdf
            self._render_result(self.current_result)
            self.status.setText("Loaded a saved result from local history.")

    def _export(self, kind: str) -> None:
        if not self.current_result:
            QMessageBox.information(self, "No summary", "Summarize a PDF or open an item from History first."); return
        if kind == "copy":
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(self.current_result.get("summary", ""))
            self.status.setText("Summary copied to clipboard."); return
        ext_map = {"txt": ("Text file (*.txt)", ".txt"), "md": ("Markdown file (*.md)", ".md"), "pdf": ("PDF file (*.pdf)", ".pdf"), "docx": ("Word document (*.docx)", ".docx")}
        file_filter, extension = ext_map[kind]
        base_dir = Path(self.config.get("output_directory", str(Path.home())))
        try: base_dir.mkdir(parents=True, exist_ok=True)
        except OSError: base_dir = Path.home()
        default_name = f"{Path(self.current_result.get('source_path', 'summary')).stem}_summary{extension}"
        path, _ = QFileDialog.getSaveFileName(self, "Save summary", str(base_dir / default_name), file_filter)
        if not path: return
        try:
            if kind == "txt": save_txt(self.current_result, path)
            elif kind == "md": save_markdown(self.current_result, path)
            elif kind == "docx": save_docx(self.current_result, path)
            elif kind == "pdf": save_pdf(self.current_result, path)
            self.status.setText(f"Saved: {path}")
            QMessageBox.information(self, "Export complete", f"Summary saved to:\n{path}")
        except Exception as exc:
            logger.exception("Export failed")
            QMessageBox.critical(self, "Export failed", f"Could not save this format.\n\n{exc}")

    def closeEvent(self, event) -> None:
        if self.worker and self.worker.isRunning():
            # Keep the QThread object alive until it exits; destroying a running QThread can crash Qt.
            self._close_when_done = True
            self.worker.requestInterruption()
            self.status.setText("Stopping the current task before closing. The active model call may need to finish first…")
            event.ignore()
            return
        event.accept()
