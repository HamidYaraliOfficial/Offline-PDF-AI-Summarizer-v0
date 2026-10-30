from __future__ import annotations
from typing import Any


def sections(result: Any) -> list[tuple[str, str]]:
    get = (lambda key, default="": result.get(key, default)) if isinstance(result, dict) else (lambda key, default="": getattr(result, key, default))
    output = [
        ("Summary", get("summary")),
        ("Key Points", get("key_points")),
        ("Important Concepts", get("important_concepts")),
        ("Keywords", get("keywords")),
    ]
    chapters = get("chapter_summaries", []) or []
    if chapters:
        output.append(("Chapter Summaries", "\n\n".join(f"{item.get('title', 'Section')}\n{item.get('summary', '')}" for item in chapters)))
    warnings = get("warnings", []) or []
    if warnings:
        output.append(("Processing Notes", "\n".join(warnings)))
    return output


def header(result: Any) -> str:
    get = (lambda key, default="": result.get(key, default)) if isinstance(result, dict) else (lambda key, default="": getattr(result, key, default))
    return f"{get('title', 'PDF Summary')}\nPages: {get('page_count', '')}\nLanguage: {get('language', '')}\nProcessing time: {get('processing_seconds', '')} seconds\n"
