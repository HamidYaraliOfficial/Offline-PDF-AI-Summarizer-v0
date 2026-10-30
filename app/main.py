from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from app.ui.main_window import MainWindow
from app.utils.logger import setup_logging


def main() -> int:
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("Offline PDF AI Summarizer")
    app.setOrganizationName("Hamid Yarali")
    app.setApplicationVersion("1.0.0")
    try:
        window = MainWindow()
        window.show()
        return app.exec()
    except Exception as exc:  # Last-resort startup guard; details are in the local log.
        QMessageBox.critical(None, "Startup error", f"The application could not start.\n\n{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
