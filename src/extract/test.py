import langextract as lx
import textwrap
from pathlib import Path
import json

prompt = textwrap.dedent("""
You are a precise clinical data extraction engine.
Extract information ONLY from the Clinical Notes provided. Do NOT extract from the example.

For EACH medication found, output one record containing ALL of the following fields:

PATIENT-LEVEL FIELDS (same value repeated for every medication belonging to this patient):
- Patient ID               : Starts with 'P' followed by digits (e.g., P700)
- Patient Full Name        : Full name as written
- Age                      : Numeric value only (e.g., 65)
- Gender                   : Infer from pronouns (he/his → Male, she/her → Female) if not stated explicitly
- Ethnicity                : Extract if stated; otherwise use "Not stated"

MEDICATION-LEVEL FIELDS (found under 'Past Medical History' section):
- Prescribed Medication ID             : Starts with 'M' followed by digits (e.g., M101)
- Prescribed Medication Name and Dosage: e.g., Amlodipine 5mg
- Prescribed Medication Start Date     : DD/MM/YYYY format
- Prescribed Medication End Date       : DD/MM/YYYY format
- Condition                            : The condition heading above this medication

RULES:
- Extract ALL medications. Do not skip any.
- If Age, Gender, or Ethnicity are truly absent with no clues, use "Not stated".
- Never return null or omit a field. Every field must have a value.
- Dates must strictly be in DD/MM/YYYY format.
- Do NOT infer medication details. Extract only what is explicitly written.

You MUST respond with valid JSON in this exact format and nothing else:
{"extractions": [{"extraction_class": "...", "extraction_text": "..."}, ...]}
""")

examples = [
    lx.data.ExampleData(
        text=(
            "THIS IS AN EXAMPLE. DO NOT EXTRACT FROM THIS.\n"
            "Patient P12345, Lim Boon Keng, 65 yo\n"
            "**Past Medical History**\n"
            "1. Hypertension diagnosed in 2018\n"
            "    - Medication ID: M101 - Amlodipine 5mg\n"
            "    - Start Date: 01/03/2018\n"
            "    - End Date: 01/03/2019\n"
            "    - Duration: 365 days\n"
            "    - Medication ID: M102 - Lisinopril 10mg\n"
            "    - Start Date: 02/03/2019\n"
            "    - End Date: 02/03/2021\n"
            "    - Duration: 730 days\n"
            "2. Hyperlipidemia diagnosed in 2020\n"
            "    - Medication ID: M205 - Atorvastatin 10mg\n"
            "    - Start Date: 15/06/2020\n"
            "    - End Date: 15/06/2025\n"
            "    - Duration: 1825 days\n"
        ),
        extractions=[
            # Patient fields
            lx.data.Extraction(extraction_class="Patient ID",    extraction_text="P12345"),
            lx.data.Extraction(extraction_class="Patient Name",  extraction_text="Lim Boon Keng"),
            lx.data.Extraction(extraction_class="Age",           extraction_text="65"),
            lx.data.Extraction(extraction_class="Gender",        extraction_text="Male"),
            lx.data.Extraction(extraction_class="Ethnicity",     extraction_text="Chinese"),
            # Medication 1
            lx.data.Extraction(extraction_class="Prescribed Medication ID",              extraction_text="M101"),
            lx.data.Extraction(extraction_class="Prescribed Medication Name and Dosage", extraction_text="Amlodipine 5mg"),
            lx.data.Extraction(extraction_class="Prescribed Medication Start Date",      extraction_text="01/03/2018"),
            lx.data.Extraction(extraction_class="Prescribed Medication End Date",        extraction_text="01/03/2019"),
            lx.data.Extraction(extraction_class="Condition",                             extraction_text="Hypertension"),
            # Medication 2
            lx.data.Extraction(extraction_class="Prescribed Medication ID",              extraction_text="M102"),
            lx.data.Extraction(extraction_class="Prescribed Medication Name and Dosage", extraction_text="Lisinopril 10mg"),
            lx.data.Extraction(extraction_class="Prescribed Medication Start Date",      extraction_text="02/03/2019"),
            lx.data.Extraction(extraction_class="Prescribed Medication End Date",        extraction_text="02/03/2021"),
            lx.data.Extraction(extraction_class="Condition",                             extraction_text="Hypertension"),
            # Medication 3
            lx.data.Extraction(extraction_class="Prescribed Medication ID",              extraction_text="M205"),
            lx.data.Extraction(extraction_class="Prescribed Medication Name and Dosage", extraction_text="Atorvastatin 10mg"),
            lx.data.Extraction(extraction_class="Prescribed Medication Start Date",      extraction_text="15/06/2020"),
            lx.data.Extraction(extraction_class="Prescribed Medication End Date",        extraction_text="15/06/2025"),
            lx.data.Extraction(extraction_class="Condition",                             extraction_text="Hyperlipidemia"),
        ],
    )
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_synopsis_texts(data_dir: Path) -> list[tuple[int, str]]:
    texts = []
    for i in range(1, 11):
        file_path = data_dir / f"Synopsis {i}.txt"
        if not file_path.is_file():
            print(f"  ⚠️ Synopsis {i}.txt not found, skipping.")
            continue
        texts.append((i, file_path.read_text(encoding="utf-8")))
    return texts


def convert_to_json(extractions) -> list[dict]:
    structured = []
    for e in extractions:
        item = {"class": e.extraction_class, "text": e.extraction_text}
        if e.attributes:
            item["attributes"] = e.attributes
        structured.append(item)
    return structured


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir     = project_root / "Data"
    output_dir   = project_root / "outputs"
    output_dir.mkdir(exist_ok=True)

    synopsis_texts = load_synopsis_texts(data_dir)

    for idx, input_text in synopsis_texts:
        print("=" * 80)
        print(f"Synopsis {idx}  ({len(input_text)} chars)")
        print("=" * 80)

        try:
            result = lx.extract(
                text_or_documents=input_text,
                prompt_description=prompt,
                examples=examples,
                model_id="gemma-local",
                model_url="http://localhost:11434",
                fence_output=False,
                use_schema_constraints=True,
            )

            structured_output = convert_to_json(result.extractions)
            output_file = output_dir / f"synopsis_{idx}.json"

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(structured_output, f, indent=2)

            print(f"  ✓ {len(result.extractions)} entities → {output_file}\n")

        except Exception as e:
            print(f"  ✗ Synopsis {idx} failed: {e}\n")
            continue


if __name__ == "__main__":
    main()