import langextract as lx
import textwrap
from pathlib import Path

# -----------------------------------
# Prompt
# -----------------------------------
prompt = textwrap.dedent("""
You must extract the following information from the given Clinical Notes provided.
    1. Patient ID
    2. Patient name
    3. Patient Age
    4. Patient Gender
    5. Patient Ethnicity
    6. Medication ID prescribed to patient
    7. Medication prescribed to patient, including dosage (if mentioned)
    8. Start Date of medication course (if mentioned)
    9. End Date of medication course (if mentioned)
    10. Length of medication course (if mentioned)
    11. Condition patient suffered from
    12. Symptoms patient experienced

Use exact text spans from the original text. Do not paraphrase.
Return entities in the order they appear.
""")

# -----------------------------------
#Few-shot Example
# -----------------------------------
examples = [
    lx.data.ExampleData(
        text=(
            "Patient ID: P700. "
            "Mr Tan Wei Ming is a 58-year-old Chinese male who was diagnosed with Hypertension on 15 March 2025 after presenting with dizziness."
            "The trigger symptom was dizziness. "
            "He was started on Drug ID 12 – Amlodipine 5mg once daily, "
            "with a prescription start date of 15 March 2025, "
            "for a duration of 180 days, and an expected end date of 11 September 2025."
        ),
        extractions=[
            lx.data.Extraction(
                extraction_class="Patient ID",
                extraction_text="P700"
            ),
            lx.data.Extraction(
                extraction_class="Patient Name",
                extraction_text="Tan Wei Ming"
            ),
            lx.data.Extraction(
                extraction_class="Age",
                extraction_text="58"
            ),
            lx.data.Extraction(
                extraction_class="Gender",
                extraction_text="male"
            ),
            lx.data.Extraction(
                extraction_class="Ethnicity",
                extraction_text="Chinese"
            ),
            lx.data.Extraction(
                    extraction_class="Prescribed Medication ID",
                    extraction_text="12"
            ),
            lx.data.Extraction(
                extraction_class="Prescribed Medication Name and Dosage",
                extraction_text="Amlodipine 5mg"
            ),
            lx.data.Extraction(
                extraction_class="Prescribed Medication Start Date",
                extraction_text="15 March 2025"
            ),
            lx.data.Extraction(
                extraction_class="Prescribed Medication End Date",
                extraction_text="11 September 2025"
            ),
            lx.data.Extraction(
                extraction_class="Prescribed Medication Duration",
                extraction_text="180 days"
            ),
            lx.data.Extraction(
                extraction_class="Condition",
                extraction_text="Hypertension"
            ),
            lx.data.Extraction(
                extraction_class="Symptom",
                extraction_text="dizziness"
            )
        ],
    )
]

def load_synopsis_texts(data_dir: Path) -> list[str]:
    """Load Clinical Text from 'Synopsis 1.txt' to 'Synopsis 10.txt' in the given folder."""
    texts: list[str] = []
    for i in range(1, 11):
        file_path = data_dir / f"Synopsis {i}.txt"
        if not file_path.is_file():
            # Skip missing files but continue with the rest
            continue
        texts.append(file_path.read_text(encoding="utf-8"))
    return texts


def main() -> None:
    # -----------------------------------
    # Input Texts from Data folder
    # -----------------------------------
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "Data"

    synopsis_texts = load_synopsis_texts(data_dir)


    # -------------------------------
    # Run LangExtract for each synopsis
    # -----------------------------------
    for idx, input_text in enumerate(synopsis_texts, start=1):
        print("=" * 80)
        print(f"Synopsis {idx}")
        print("=" * 80)

        result = lx.extract(
            text_or_documents=input_text,
            prompt_description=prompt,
            examples=examples,
            model_id="gemma-3-4b-it-Q4_K_M:latest",
            fence_output=False,
            use_schema_constraints=False,
        )

        print(f"\nInput:\n{input_text}\n")
        print("Extracted entities:\n")

        for entity in result.extractions:
            position_info = ""
            if entity.char_interval:
                start = entity.char_interval.start_pos
                end = entity.char_interval.end_pos
                position_info = f" (pos: {start}-{end})"

            print(
                f"• {entity.extraction_class}: {entity.extraction_text}{position_info}"
            )

            if entity.attributes:
                print(f"   Attributes: {entity.attributes}")


if __name__ == "__main__":
    main()