import langextract as lx
import textwrap
from pathlib import Path

# -----------------------------------
# Prompt
# -----------------------------------
prompt = textwrap.dedent("""
You are a precise clinical data extraction engine. Your task is to extract specific information **ONLY** from the provided Clinical Notes.
                         
**Task:**
You must extract *ALL* of the following information **ONLY** from the given Clinical Notes provided.
    1. Patient ID - Unique Patient Identifier (e.g., P700)
    2. Patient Name - Full name of the patient
    3. Patient Age - Age of the patient in years
    4. Patient Gender - Gender of the patient (Male/Female)
    5. Patient Ethnicity - Ethnicity of the patient 
    6. Medication ID prescribed to patient - Unique Identifier for the medication (e.g., M228)
    7. Medication Name prescribed to patient - Full medication name, including the dosage (e.g., Amlodipine 5mg)
    8. Start Date of medication course - Start date for the medication (DD/MM/YYYY)
    9. End Date of medication course - End date for the medication (DD/MM/YYYY)
    10. Medical Condition(s) patient suffered from - The specific condition this medication was prescribed for (e.g., Hypertension)

**Extraction Guidelines:**
- **Completeness**: Extract ALL medications present. Do not skip any entry.
- **Dates**: Standardize all dates to the format DD/MM/YYYY. 
- **Map medication to condition**: 
                         
**Output Format:** 
- Return a JSON array where each element
                         

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


def main():
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
            model_id="gemma-local",
            model_url="http://localhost:11434",
            fence_output=False,
            use_schema_constraints=False,
        )

        print("Extracted entities:\n")


if __name__ == "__main__":
    main()