from __future__ import annotations

LANGUAGE_NAMES = {"fa": "Persian", "en": "English", "zh": "Chinese", "auto": "the source document's language"}


def chunk_system(language: str) -> str:
    return ("You are a careful document summarizer. Summarize only what is supported by the supplied text. "
            "Preserve important qualifications, numbers, named entities, and uncertainty. Do not invent facts. "
            f"Write in {LANGUAGE_NAMES.get(language, language)}. The text may contain OCR mistakes; do not silently guess missing facts.")


def final_system(language: str) -> str:
    return ("You are an evidence-faithful PDF summarizer. Use only the supplied notes; never claim to have read material not represented in them. "
            f"Write the content in {LANGUAGE_NAMES.get(language, language)}. "
            "Output exactly these four headings as separate lines, preserving the English heading text so the application can parse it: "
            "SUMMARY, KEY POINTS, IMPORTANT CONCEPTS, KEYWORDS. "
            "Under KEY POINTS use a concise bullet list, under IMPORTANT CONCEPTS list terms with brief explanations, "
            "and under KEYWORDS provide comma-separated terms. Do not add a preamble.")


def make_chunk_prompt(text: str, summary_type: str, section: str = "") -> str:
    length = {
        "short": "Write a compact summary in 3-5 sentences.",
        "standard": "Write a balanced summary covering the main argument, methods, evidence, and conclusions when present.",
        "detailed": "Write a detailed structured summary with essential subtopics, evidence, caveats, and conclusions.",
        "chapter": "Summarize this section carefully, keeping its central ideas and useful details.",
    }.get(summary_type, "Write a balanced summary.")
    prefix = f"Section heading: {section}\n" if section and section != "Document" else ""
    return f"{length}\n{prefix}Summarize the following PDF text faithfully:\n\n{text}"
