import langextract as lx
import textwrap
from pathlib import Path
import json
from langextract.providers import ollama

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
    7. Medication Name prescribed to patient - Full medication name (e.g., Amlodipine)
    8. Start Date of medication course - Start date for the medication (DD/MM/YYYY)
    9. End Date of medication course - End date for the medication (DD/MM/YYYY)
    10. Medical Condition(s) patient suffered from - The specific condition this medication was prescribed for (e.g., Hypertension)

**Extraction Guidelines:**
- **Completeness**: Extract ALL medications present. Do not skip any entry.
- **Dates**: Standardize all dates to the format DD/MM/YYYY. 
- **Extract only spans that appear exactly in the current input clinical note. Never copy values from examples. Examples are only to illustrate the output format. **
                         
**Output Format:** 
- Extract entities as labeled spans according to the schema.
- Each entity should correspond to one of the extraction classes listed above.
""")

examples = [
    lx.data.ExampleData(
        text=(
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
        ),
        extractions=[
            lx.data.Extraction(extraction_class="Patient ID", extraction_text="P12345"),
            lx.data.Extraction(extraction_class="Patient Name",extraction_text="Lim Boon Keng"),
            lx.data.Extraction(extraction_class="Patient Age",extraction_text="65"),
            lx.data.Extraction(extraction_class="Patient Gender",extraction_text="Male"),
            lx.data.Extraction(extraction_class="Patient Ethnicity",extraction_text="Chinese"),

            # Medication 1
            lx.data.Extraction(extraction_class="Medication ID prescribed to patient",extraction_text="M101"),
            lx.data.Extraction(extraction_class="Medication Name prescribed to patient",extraction_text="Amlodipine"),
            lx.data.Extraction(extraction_class="Start Date of medication course",extraction_text="01/03/2018"),
            lx.data.Extraction(extraction_class="End Date of medication course",extraction_text="01/03/2019"),
            lx.data.Extraction(extraction_class="Medical Condition(s) patient suffered from",extraction_text="Hypertension"),

            # Medication 2
            lx.data.Extraction(extraction_class="Medication ID prescribed to patient",extraction_text="M102"),
            lx.data.Extraction(extraction_class="Medication Name prescribed to patient",extraction_text="Lisinopril"),
            lx.data.Extraction(extraction_class="Start Date of medication course",extraction_text="02/03/2019"),
            lx.data.Extraction(extraction_class="End Date of medication course",extraction_text="02/03/2021"),
            lx.data.Extraction(extraction_class="Medical Condition(s) patient suffered from",extraction_text="Hypertension")
        ],
    )
]

allowed_classes = {
    "Patient ID",
    "Patient Name",
    "Patient Age",
    "Patient Gender",
    "Patient Ethnicity",
    "Medication ID prescribed to patient",
    "Medication Name prescribed to patient",
    "Start Date of medication course",
    "End Date of medication course",
    "Medical Condition(s) patient suffered from",
}

def load_synopsis_texts(data_dir: Path) -> list[tuple[str, str]]:
    texts: list[tuple[str, str]] = []
    for file_path in sorted(data_dir.glob("*.txt")):
        texts.append((file_path.stem, file_path.read_text(encoding="utf-8")))
    return texts


def convert_to_json(extraction_result):
    return [
        {
            "class": e.extraction_class,
            "text": e.extraction_text,
            **({"attributes": e.attributes} if e.attributes else {})
        }
        for e in extraction_result.extractions
    ]

def flatten_extractions_to_record(flat_data: list[dict]) -> dict:
    record = {
        "patient_id": "",
        "patient_name": "",
        "patient_age": "",
        "patient_gender": "",
        "patient_ethnicity": "",
        "medications": []
    }

    current_med = {}

    patient_field_map = {
        "Patient ID": "patient_id",
        "Patient Name": "patient_name",
        "Patient Age": "patient_age",
        "Patient Gender": "patient_gender",
        "Patient Ethnicity": "patient_ethnicity",
    }

    medication_field_map = {
        "Medication ID prescribed to patient": "medication_id",
        "Medication Name prescribed to patient": "medication_name",
        "Start Date of medication course": "start_date",
        "End Date of medication course": "end_date",
        "Medical Condition(s) patient suffered from": "condition",
    }

    medication_order = [
        "medication_id",
        "medication_name",
        "start_date",
        "end_date",
        "condition",
    ]

    for item in flat_data:
        cls = item.get("class", "").strip()
        text = item.get("text", "").strip()

        if cls in patient_field_map:
            record[patient_field_map[cls]] = text

        elif cls in medication_field_map:
            field_name = medication_field_map[cls]

            if field_name == "medication_id" and current_med:
                record["medications"].append(current_med)
                current_med = {}

            current_med[field_name] = text

            if all(key in current_med for key in medication_order):
                record["medications"].append(current_med)
                current_med = {}

    if current_med:
        record["medications"].append(current_med)

    return record


def run_extraction(input_dir: Path, output_dir: Path):
    synopsis_texts = load_synopsis_texts(input_dir)

    if not synopsis_texts:
        raise FileNotFoundError(f"No synopsis text files found in {input_dir}")

    for idx, (file_stem, input_text) in enumerate(synopsis_texts, start=1):
        print("=" * 80)
        print(f"Synopsis {idx}")
        print("=" * 80)

        try:
            result = lx.extract(
            text_or_documents=input_text,
            prompt_description=prompt,
            examples=examples,
            model_id="gemma-local",
            model_url="http://localhost:11434",
            temperature = 0,
            language_model_params={"top_p": 0.2, "num_ctx": 4096, "top_k": 10, "num_predict": -1},
            max_char_buffer=2500,
            fence_output=False,
            use_schema_constraints=False,
            max_workers=2,
            batch_length=2,
            show_progress=True,
            resolver_params={"format_handler": ollama.OLLAMA_FORMAT_HANDLER}
        )

        except Exception as error:
            print(f"Error processing Synopsis {idx}: {error}")
            continue    

        valid_extractions = [
            e for e in result.extractions
            if e.extraction_class in allowed_classes
            and str(e.extraction_text) in input_text
        ]
        result.extractions = valid_extractions

        print("Extracted entities:\n")
        print(result.extractions)

        structured_output = convert_to_json(result)
        structured_record = flatten_extractions_to_record(structured_output)
 
        output_file = output_dir / f"{file_stem}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(structured_record, f, indent=2)

        print(f"Saved JSON to {output_file}")


if __name__ == "__main__":
    run_extraction()
    # project_root = Path(__file__).resolve().parents[2]
    # run_extraction(
    #     project_root / "outputs" / "preprocessed_notes",
    #     project_root / "outputs" / "extracted_entities"
    # )