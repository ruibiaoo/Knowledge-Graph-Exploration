import os
import textwrap
from pathlib import Path

import langextract as lx
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found. Put it in a .env file or set it as an env var.")

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
""").strip()


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


DATA_DIR = Path("Data")  # <-- matches your folder name

for i in range(1, 11):
    fp = DATA_DIR / f"Synopsis {i}.txt"
    if not fp.is_file():
        print(f"Missing: {fp}")
        continue

    input_text = fp.read_text(encoding="utf-8")

    result = lx.extract(
        text_or_documents=input_text,      # <-- key: use this, not `texts=`
        prompt_description=prompt,         # <-- match your example
        examples=examples,
        model_id="gemini-2.5-flash",
        api_key=GOOGLE_API_KEY,            # include if your setup needs it
    )

    print(f"\n=== Synopsis {i} ===")
    # result might be list-like depending on version; handle both:
    extractions = getattr(result, "extractions", None)
    if extractions is None and isinstance(result, list) and len(result) > 0:
        extractions = result[0].extractions

    for ent in (extractions or []):
        span = ""
        if getattr(ent, "char_interval", None):
            span = f" ({ent.char_interval.start_pos}-{ent.char_interval.end_pos})"
        print(f"• {ent.extraction_class}: {ent.extraction_text}{span}")
