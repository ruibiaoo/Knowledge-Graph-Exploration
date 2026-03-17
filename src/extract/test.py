import langextract as lx
import textwrap
from pathlib import Path
import json

# ── Prompt ────────────────────────────────────────────────────────────────────
# Shorter prompt = fewer tokens = faster inference on a 27B model

prompt = textwrap.dedent("""
You are a clinical data extraction engine. Extract ONLY from the Clinical Notes below.

Extract these fields for EACH medication:
1. Patient ID
2. Patient Full Name
3. Patient Age (number only)
4. Patient Gender (Male/Female)
5. Patient Ethnicity
6. Medication ID (e.g. M228)
7. Medication Name and Dosage (e.g. Metformin 850mg)
8. Medication Start Date (DD/MM/YYYY)
9. Medication End Date (DD/MM/YYYY)
10. Condition (the condition this medication treats)

Rules:
- Extract ALL medications. Do not skip any.
- Dates must be DD/MM/YYYY.
- Only extract what is explicitly stated.
""")

# ── Examples ──────────────────────────────────────────────────────────────────
# Keep ONE clear example — enough to show structure without bloating token count

examples = [
    lx.data.ExampleData(
        text=(
            "[EXAMPLE — learn format only, do NOT extract this]\n"
            "Patient P12345, Lim Boon Keng, 65 yo, Chinese Male.\n"
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
            "[END EXAMPLE]\n"
        ),
        extractions=[
            lx.data.Extraction(extraction_class="Patient ID",                       extraction_text="P12345"),
            lx.data.Extraction(extraction_class="Patient Name",                     extraction_text="Lim Boon Keng"),
            lx.data.Extraction(extraction_class="Age",                              extraction_text="65"),
            lx.data.Extraction(extraction_class="Gender",                           extraction_text="Male"),
            lx.data.Extraction(extraction_class="Ethnicity",                        extraction_text="Chinese"),
            lx.data.Extraction(extraction_class="Prescribed Medication ID",         extraction_text="M101"),
            lx.data.Extraction(extraction_class="Prescribed Medication Name and Dosage", extraction_text="Amlodipine 5mg"),
            lx.data.Extraction(extraction_class="Prescribed Medication Start Date", extraction_text="01/03/2018"),
            lx.data.Extraction(extraction_class="Prescribed Medication End Date",   extraction_text="01/03/2019"),
            lx.data.Extraction(extraction_class="Condition",                        extraction_text="Hypertension"),
            lx.data.Extraction(extraction_class="Prescribed Medication ID",         extraction_text="M102"),
            lx.data.Extraction(extraction_class="Prescribed Medication Name and Dosage", extraction_text="Lisinopril 10mg"),
            lx.data.Extraction(extraction_class="Prescribed Medication Start Date", extraction_text="02/03/2019"),
            lx.data.Extraction(extraction_class="Prescribed Medication End Date",   extraction_text="02/03/2021"),
            lx.data.Extraction(extraction_class="Condition",                        extraction_text="Hypertension"),
            lx.data.Extraction(extraction_class="Prescribed Medication ID",         extraction_text="M205"),
            lx.data.Extraction(extraction_class="Prescribed Medication Name and Dosage", extraction_text="Atorvastatin 10mg"),
            lx.data.Extraction(extraction_class="Prescribed Medication Start Date", extraction_text="15/06/2020"),
            lx.data.Extraction(extraction_class="Prescribed Medication End Date",   extraction_text="15/06/2025"),
            lx.data.Extraction(extraction_class="Condition",                        extraction_text="Hyperlipidemia"),
        ],
    )
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_synopsis_texts(data_dir: Path) -> list[str]:
    texts: list[str] = []
    for i in range(1, 11):
        file_path = data_dir / f"Synopsis {i}.txt"
        texts.append(file_path.read_text(encoding="utf-8"))
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

    for idx, input_text in enumerate(synopsis_texts, start=1):
        print("=" * 80)
        print(f"Synopsis {idx}  ({len(input_text)} chars)")
        print("=" * 80)

        result = lx.extract(
            text_or_documents=input_text,
            prompt_description=prompt,
            examples=examples,
            model_id="gemma-local",
            model_url="http://localhost:11434",
            fence_output=False,
            use_schema_constraints=False,  # True adds overhead, off is faster
        )

        structured_output = convert_to_json(result.extractions)

        output_file = output_dir / f"synopsis_{idx}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(structured_output, f, indent=2)

        print(f"  ✓ {len(result.extractions)} entities → {output_file}\n")


if __name__ == "__main__":
    main()