import boto3
import textwrap
from pathlib import Path

# -----------------------------------
# AWS Comprehend Client
# -----------------------------------
comprehend = boto3.client(
    service_name="comprehend",
    region_name="ap-southeast-1"
)

# -----------------------------------
# Prompt (kept for documentation)
# -----------------------------------
prompt = textwrap.dedent("""
You must extract the following information from the given Clinical Notes provided.
    1. Patient ID
    2. Patient name
    3. Patient Age
    4. Patient Gender
    5. Patient Ethnicity
    6. Medication ID prescribed to patient
    7. Medication prescribed to patient, including dosage and frequency (if mentioned)
    8. Start Date of medication course (if mentioned)
    9. End Date of medication course (if mentioned)
    10. Length of medication course (if mentioned)
    11. Condition patient suffered from
    12. Symptoms patient experienced 
""")

def load_synopsis_texts(data_dir: Path) -> list[str]:
    """Load Clinical Text from 'Synopsis 1.txt' to 'Synopsis 10.txt'."""
    texts: list[str] = []
    for i in range(1, 11):
        file_path = data_dir / f"Synopsis {i}.txt"
        if not file_path.is_file():
            continue
        texts.append(file_path.read_text(encoding="utf-8"))
    return texts


def extract_entities_aws(text: str):
    response = comprehend.detect_entities(
        Text=text,
        LanguageCode="en"
    )

    entities = []

    for entity in response["Entities"]:
        entities.append({
            "text": entity["Text"],
            "type": entity["Type"],
            "score": entity["Score"],
            "start": entity["BeginOffset"],
            "end": entity["EndOffset"]
        })

    return entities


def main() -> None:

    # -----------------------------------
    # Input Texts
    # -----------------------------------
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "Data"

    synopsis_texts = load_synopsis_texts(data_dir)

    # -----------------------------------
    # Run AWS Comprehend
    # -----------------------------------
    for idx, input_text in enumerate(synopsis_texts, start=1):

        print("=" * 80)
        print(f"Synopsis {idx}")
        print("=" * 80)

        print("\nInput:\n")
        print(input_text)

        print("\nExtracted entities:\n")

        entities = extract_entities_aws(input_text)

        for ent in entities:
            print(
                f"• {ent['text']} "
                f"[{ent['type']}] "
                f"(confidence: {ent['score']:.3f}) "
                f"(pos: {ent['start']}-{ent['end']})"
            )

if __name__ == "__main__":
    main()