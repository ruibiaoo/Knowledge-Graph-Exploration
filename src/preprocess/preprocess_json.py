from pathlib import Path
import re
import json

## Extract relevant categories from the original notes
def json_to_text(file_path: Path) -> str:
    data = json.loads(file_path.read_text(encoding="utf-8"))

    content = data.get("content", {})
    sections = []

    ed = content.get("contentEDSummary", {})
    ds = content.get("contentDischargeSummary", {})

    target_sections = [
        ed.get("Consultation", {}).get("ConsultationNotes", []),
        ed.get("Triage", {}).get("TriageNotes", []),
        ds.get("ClinicalSynopsis", []),
    ]

    for section in target_sections:
        for entry in section:
            if isinstance(entry, dict) and entry.get("Notes"):
                sections.append(entry["Notes"])
            elif isinstance(entry, str):
                sections.append(entry)

    return "\n\n".join(sections)


# HTML Stripping
def strip_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)  # strip all other tags
    return text.strip()


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
def preprocess_notes_json(input_dir: Path, output_dir: Path):

    json_files = sorted(input_dir.glob("*.json"))
    for file_path in json_files:
        raw_text = json_to_text(file_path)
        stripped_text = strip_html(raw_text)
        cleaned_text = clean_text(stripped_text)
        negated_phrases = sorted(detect_negated_phrases(cleaned_text))

        cleaned_output_file = output_dir / f"{file_path.stem}_cleaned.txt"
        negation_output_file = output_dir / f"{file_path.stem}_negations.json"

        cleaned_output_file.write_text(cleaned_text, encoding="utf-8")
        negation_output_file.write_text(json.dumps(negated_phrases, indent=2), encoding="utf-8")

        print(f"Preprocessed {file_path.name} -> {cleaned_output_file.name}, {negation_output_file.name}")

# Main preprocessing function
if __name__ == "__main__":
    preprocess_notes_json()
    # project_root = Path(__file__).resolve().parents[2]
    # preprocess_notes_txt(
    #     project_root / "Data",
    #     project_root / "outputs" / "preprocessed_notes"
    # )