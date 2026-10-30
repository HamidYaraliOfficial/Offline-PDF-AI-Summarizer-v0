from pathlib import Path
from app.export.common import header, sections


def save_markdown(result, path: str | Path) -> None:
    content = [f"# {header(result).splitlines()[0]}\n", header(result).split("\n", 1)[1]]
    for title, body in sections(result):
        content.append(f"\n## {title}\n\n{body or 'Not provided.'}\n")
    Path(path).write_text("\n".join(content), encoding="utf-8")
