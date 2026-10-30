from __future__ import annotations

import html
from pathlib import Path
from PySide6.QtCore import QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize, QPdfWriter, QTextDocument
from app.export.common import sections


def save_pdf(result, path: str | Path) -> None:
    """Export via Qt's Unicode-capable text renderer, which handles more scripts than Helvetica-only PDF fonts."""
    get = (lambda key, default="": result.get(key, default)) if isinstance(result, dict) else (lambda key, default="": getattr(result, key, default))
    parts = [f"<h1>{html.escape(str(get('title', 'PDF Summary')))}</h1>"]
    parts.append(f"<p>Pages: {html.escape(str(get('page_count', '')))} | Language: {html.escape(str(get('language', '')))} | Processing time: {html.escape(str(get('processing_seconds', '')))} seconds</p>")
    for title, body in sections(result):
        parts.append(f"<h2>{html.escape(title)}</h2>")
        safe_body = html.escape(body or "Not provided.").replace("\n", "<br>")
        parts.append(f"<div>{safe_body}</div>")
    writer = QPdfWriter(str(Path(path)))
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setPageLayout(QPageLayout(QPageSize(QPageSize.PageSizeId.A4), QPageLayout.Orientation.Portrait, QMarginsF(18, 18, 18, 18)))
    document = QTextDocument()
    document.setHtml("<html><head><meta charset='utf-8'><style>body{font-family:Arial,sans-serif;font-size:10pt} h1{font-size:20pt} h2{font-size:14pt;margin-top:18pt} div{white-space:pre-wrap}</style></head><body>" + "".join(parts) + "</body></html>")
    document.print_(writer)
