import langextract as lx
import textwrap
from pathlib import Path
import json

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
                         
**Output Format:** 
- Extract entities as labeled spans according to the schema.
- Each entity should correspond to one of the extraction classes listed above.
""")

examples = [
    lx.data.ExampleData(
        text=(
        "**THIS IS AN EXAMPLE CLINICAL NOTE FOR DEMONSTRATION PURPOSES ONLY**\n"
        "DO NOT EXTRACT ANY INFORMATION FROM THIS EXAMPLE CLINICAL NOTE. ONLY EXTRACT FROM THE PROVIDED CLINICAL NOTES.\n\n"
        "Patient P12345, S9876543A, K9876541H, Lim Boon Keng, 65 yo, Chinese Male lives with "
        "his wife in Bedok, Singapore.\n"
        "**Past Medical History**\n"
        "1. Hypertension diagnosed in 2018\n"
        "    - Medication ID: M101 - Amlodipine 5mg\n"
        "    - Start Date: 01/03/2018\n"
        "    - End Date: 01/03/2019\n"
        "    - Medication ID: M102 - Lisinopril 10mg\n"
        "    - Start Date: 02/03/2019\n"
        "    - End Date: 02/03/2021\n"
        "2. Hyperlipidemia diagnosed in 2020\n"
        "    - Medication ID: M205 - Atorvastatin 10mg\n"
        "    - Start Date: 15/06/2020\n"
        "    - End Date: 15/06/2025\n"
        ),
        extractions=[
            lx.data.Extraction(extraction_class="Patient ID", extraction_text="P12345"),
            lx.data.Extraction(extraction_class="Patient Name",extraction_text="Lim Boon Keng"),
            lx.data.Extraction(extraction_class="Age",extraction_text="65"),
            lx.data.Extraction(extraction_class="Gender",extraction_text="Male"),
            lx.data.Extraction(extraction_class="Ethnicity",extraction_text="Chinese"),

            # Medication 1
            lx.data.Extraction(extraction_class="Prescribed Medication ID",extraction_text="M101"),
            lx.data.Extraction(extraction_class="Prescribed Medication Name and Dosage",extraction_text="Amlodipine 5mg"),
            lx.data.Extraction(extraction_class="Prescribed Medication Start Date",extraction_text="01/03/2018"),
            lx.data.Extraction(extraction_class="Prescribed Medication End Date",extraction_text="01/03/2019"),
            lx.data.Extraction(extraction_class="Condition",extraction_text="Hypertension"),

            # Medication 2
            lx.data.Extraction(extraction_class="Prescribed Medication ID",extraction_text="M102"),
            lx.data.Extraction(extraction_class="Prescribed Medication Name and Dosage",extraction_text="Lisinopril 10mg"),
            lx.data.Extraction(extraction_class="Prescribed Medication Start Date",extraction_text="02/03/2019"),
            lx.data.Extraction(extraction_class="Prescribed Medication End Date",extraction_text="02/03/2021"),
            lx.data.Extraction(extraction_class="Condition",extraction_text="Hypertension"),

            # Medication 3
            lx.data.Extraction(extraction_class="Prescribed Medication ID",extraction_text="M205"),
            lx.data.Extraction(extraction_class="Prescribed Medication Name and Dosage",extraction_text="Atorvastatin 10mg"),
            lx.data.Extraction(extraction_class="Prescribed Medication Start Date",extraction_text="15/06/2020"),
            lx.data.Extraction(extraction_class="Prescribed Medication End Date",extraction_text="15/06/2025"),
            lx.data.Extraction(extraction_class="Condition",extraction_text="Hyperlipidemia"),
        ],
    )
]

def load_synopsis_texts(data_dir: Path) -> list[str]:
    texts: list[str] = []
    for i in range(1, 11):
        file_path = data_dir / f"Synopsis {i}.txt"
        texts.append(file_path.read_text(encoding="utf-8"))
    return texts


def convert_to_json(result):
    structured = []

    for result in result.extractions:
        item = {
            "class": result.extraction_class,
            "text": result.extraction_text,
        }

        if result.attributes:
            item["attributes"] = result.attributes

        structured.append(item)
    return structured


def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "Data"
    synopsis_texts = load_synopsis_texts(data_dir)

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
            max_workers=20
        )

        print("Extracted entities:\n")
        print(result.extractions)

        structured_output = convert_to_json(result)
        output_dir = project_root / "outputs"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"synopsis_{idx}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(structured_output, f, indent=2)

        print(f"Saved JSON to {output_file}")


if __name__ == "__main__":
    main()