from pathlib import Path
import json
import logging

from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage


logger = logging.getLogger(__name__)

model = OllamaLLM(model="gemma-local", 
               temperature = 0)

template = """
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

**Few-Shot Examples:**

Input:
Patient P12345, S9876543A, K9876541H, Lim Boon Keng, 65 yo, Chinese Male lives with his wife in Bedok, Singapore.
**Past Medical History**
1. Hypertension diagnosed in 2018
    - Medication ID: M101 - Amlodipine 5mg
    - Start Date: 01/03/2018
    - End Date: 01/03/2019
    - Medication ID: M102 - Lisinopril 10mg
    - Start Date: 02/03/2019
    - End Date: 02/03/2021
2. Hyperlipidemia diagnosed in 2020
    - Medication ID: M205 - Atorvastatin 10mg
    - Start Date: 15/06/2020
    - End Date: 15/06/2025

Output:
[
  {{
    "patient_id": "P12345",
    "patient_name": "Lim Boon Keng",
    "age": 65,
    "gender": "Male",
    "ethnicity": "Chinese",
    "medication_id": "M101",
    "medication_name_dosage": "Amlodipine 5mg",
    "start_date": "01/03/2018",
    "end_date": "01/03/2019",
    "condition": "Hypertension"
  }},
  {{
    "patient_id": "P12345",
    "patient_name": "Lim Boon Keng",
    "age": 65,
    "gender": "Male",
    "ethnicity": "Chinese",
    "medication_id": "M102",
    "medication_name_dosage": "Lisinopril 10mg",
    "start_date": "02/03/2019",
    "end_date": "02/03/2021",
    "condition": "Hypertension"
  }},
  {{
    "patient_id": "P12345",
    "patient_name": "Lim Boon Keng",
    "age": 65,
    "gender": "Male",
    "ethnicity": "Chinese",
    "medication_id": "M205",
    "medication_name_dosage": "Atorvastatin 10mg",
    "start_date": "15/06/2020",
    "end_date": "15/06/2025",
    "condition": "Hyperlipidemia"
  }}
]

Return ONLY the JSON array. No explanation, no preamble, no markdown formatting.
"""

prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=template), 
    HumanMessage(content="{clinical_note}")
])


chain = prompt | model 


def load_synopsis_texts(data_dir: Path) -> list[str]:
    texts: list[str] = []
    for i in range(1, 11):
        file_path = data_dir / f"Synopsis {i}.txt"
        texts.append(file_path.read_text(encoding="utf-8"))
    return texts


def run_extraction(data_dir: Path) -> list[dict]:
    synopsis_texts = load_synopsis_texts(data_dir)
    all_results: list[dict] = []

    for idx, clinical_note in enumerate(synopsis_texts, start=1):
        logger.info(f"Processing Synopsis {idx} ...")
        result = chain.invoke({"clinical_note": clinical_note})
        clean = result.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)
        all_results.extend(parsed)
        logger.info(f"✓ Synopsis {idx}: {len(parsed)} records extracted")

    return all_results


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")

    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir     = project_root / "Data"
    output_path  = project_root / "output_extractions.json"
    all_results = run_extraction(data_dir)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"\n✓ {len(all_results)} total records saved to {output_path}")


if __name__ == "__main__":
    main()

