from __future__ import annotations

import logging
from PySide6.QtCore import QThread, Signal
from app.ai.summarizer import LocalSummarizer

logger = logging.getLogger(__name__)


class SummaryWorker(QThread):
    progress = Signal(int, str)
    succeeded = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, path: str, summary_type: str, language: str, config: dict) -> None:
        super().__init__()
        self.path = path
        self.summary_type = summary_type
        self.language = language
        self.config = dict(config)

    def run(self) -> None:
        summarizer = None
        try:
            summarizer = LocalSummarizer(self.config, self.isInterruptionRequestedProxy(), self._progress)
            result = summarizer.summarize_pdf(self.path, self.summary_type, self.language)
            self.succeeded.emit(result.to_dict())
        except InterruptedError:
            self.cancelled.emit()
        except Exception as exc:
            logger.exception("Summarization failed")
            self.failed.emit(str(exc))
        finally:
            if summarizer is not None:
                summarizer.close()

    def _progress(self, value: int, message: str) -> None:
        self.progress.emit(value, message)

    def isInterruptionRequestedProxy(self):
        """Thread-safe event facade compatible with the summarizer's cancellation interface."""
        class CancelFacade:
            def __init__(self, worker): self.worker = worker
            def is_set(self): return self.worker.isInterruptionRequested()
        return CancelFacade(self)
