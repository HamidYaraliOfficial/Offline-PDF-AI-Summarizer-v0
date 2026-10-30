from pathlib import Path
from app.export.common import header, sections


def save_txt(result, path: str | Path) -> None:
    content = [header(result)]
    for title, body in sections(result):
        content.append(f"\n{'=' * 72}\n{title}\n{'=' * 72}\n{body or 'Not provided.'}\n")
    Path(path).write_text("\n".join(content), encoding="utf-8")
