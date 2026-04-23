from __future__ import annotations
from pathlib import Path
from os import name
import re
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "Data"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "preprocessed_notes"

# Text Cleaning
PHI_PATTERNS = re.compile(
    r"\[REDACTED\]|\[NAME\]|\[DOB\]|\[ADDRESS\]|\[PHONE\]|\[EMAIL\]|\[ID\]|\[PASSPORT\]",
    re.IGNORECASE)

def clean_text(text: str) -> str:
    # Remove PHI markers
    text = PHI_PATTERNS.sub("", text)

    # Strip trailing whitespace on each line
    lines = [line.rstrip() for line in text.splitlines()]
    text = "\n".join(lines)

    # Collapse multiple blank lines to a maximum of two
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces/tabs within a line to a single space
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()


# Negation Detection
NEGATION_TRIGGERS = [
    r"no\b",
    r"not\b",
    r"den(?:y|ies|ied)\b",
    r"without\b",
    r"absence\s+of",
    r"negative\s+for",
    r"never\b",
    r"non[- ]",
    r"no\s+evidence\s+of",
    r"rul(?:e|ed)\s+out",
    r"free\s+of",
]

NEG_PATTERN = re.compile(
    r"(?:" + "|".join(NEGATION_TRIGGERS) + r")"
    r"\s+(?:\w+\s+){0,4}\w+",    # negation trigger + up to 5 following words
    re.IGNORECASE,
)

def detect_negated_phrases(text: str) -> set[str]:
    negated_phrases: set[str] = set()

    for m in NEG_PATTERN.finditer(text):
        matched_text = m.group()
        negated_phrases.add(matched_text.lower().strip())

    return negated_phrases


# Main preprocessing function
if __name__ == "__main__":

    if file
    cleaned = clean_text(raw_text)
    negation_phrases = detect_negated_phrases(cleaned)

    return cleaned.to_txt(), negation_phrases.to_json()

