from __future__ import annotations
from pathlib import Path
import re
import json

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

# Preprocessing pipeline
def preprocess_notes_txt(input_dir: Path, output_dir: Path):

    txt_files = sorted(input_dir.glob("*.txt"))
    for file_path in txt_files:
        raw_text = file_path.read_text(encoding="utf-8")
        cleaned_text = clean_text(raw_text)
        negated_phrases = sorted(detect_negated_phrases(cleaned_text))

        cleaned_output_file = output_dir / f"{file_path.stem}_cleaned.txt"
        negation_output_file = output_dir / f"{file_path.stem}_negations.json"

        cleaned_output_file.write_text(cleaned_text, encoding="utf-8")
        negation_output_file.write_text(json.dumps(negated_phrases, indent=2), encoding="utf-8")

        print(f"Preprocessed {file_path.name} -> {cleaned_output_file.name}, {negation_output_file.name}")

# Main preprocessing function
if __name__ == "__main__":
    preprocess_notes_txt()
    # project_root = Path(__file__).resolve().parents[2]
    # preprocess_notes_txt(
    #     project_root / "Data",
    #     project_root / "outputs" / "preprocessed_notes"
    # )