# RecursiveCharacterTextSplitter
from pathlib import Path
import json
import logging
import textwrap

from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter


logger = logging.getLogger(__name__)

model = OllamaLLM(model="gemma-local", 
               temperature = 0,
               num_ctx = 4096,
               num_predict = 2048,
               repeat_penalty = 1.1,
               timeout = 1200,
               seed = 42,
               num_gpu = 1,
               num_thread = 8,
               format="json"
               )

examples = [
    {
        "input": (
            "Patient P12345, Lim Boon Keng, 65 yo, Chinese Male.\n"
            "Past Medical History:\n"
            "Hypertension diagnosed in 2018\n"
            "- Medication ID: M101 - Amlodipine 5mg\n"
            "- Start Date: 01/03/2018\n"
            "- End Date: 01/03/2019\n"
            "- Medication ID: M102 - Lisinopril 10mg\n"
            "- Start Date: 02/03/2019\n"
            "- End Date: 02/03/2021\n"
        ),
        "output": """{
            "patient_id": "P12345",
            "patient_name": "Lim Boon Keng",
            "patient_age": 65,
            "patient_gender": "Male",
            "patient_ethnicity": "Chinese",
            "medications": [
                {
                "medication_id": "M101",
                "medication_name": "Amlodipine 5mg",
                "start_date": "01/03/2018",
                "end_date": "01/03/2019",
                "condition": "Hypertension"
                },
                {
                "medication_id": "M102",
                "medication_name": "Lisinopril 10mg",
                "start_date": "02/03/2019",
                "end_date": "02/03/2021",
                "condition": "Hypertension"
            }
        ]
        }"""
    }
]


example_prompt = ChatPromptTemplate.from_messages([
    ("user", "{input}"),
    ("assistant", "{output}")
])

few_shot = FewShotChatMessagePromptTemplate(
    examples=examples,
    example_prompt=example_prompt
)

prompt = ChatPromptTemplate.from_messages([
    ("system", textwrap.dedent("""
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
- **Extract only spans that appear exactly in the current input clinical note. Never copy values from examples. Examples are only to illustrate the output format. **
                         
**Output Format:** 
- Each entity should correspond to one of the extraction classes listed above.""")),
    few_shot,
    ("user", "{clinical_note}")
])

text_splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=200)

chain = prompt | model 


def load_synopsis_texts(data_dir: Path) -> list[str]:
    texts: list[str] = []
    for i in range(1, 11):
        file_path = data_dir / f"Synopsis {i}.txt"
        texts.append(file_path.read_text(encoding="utf-8"))
    return texts


def merge_results(chunk_results: list[dict]) -> dict:
    if not chunk_results:
        return {}

    merged = {
        "patient_id": None,
        "patient_name": None,
        "patient_age": None,
        "patient_gender": None,
        "patient_ethnicity": None,
        "medications": []
    }

    seen_meds = set()

    for res in chunk_results:
        # Fill patient-level info (only once)
        for key in ["patient_id", "patient_name", "patient_age", "patient_gender", "patient_ethnicity"]:
            if merged[key] is None and key in res:
                merged[key] = res[key]

    for med in res.get("medications", []):
        med_key = (
            med.get("medication_id"),
            med.get("medication_name"),
            med.get("start_date"),
            med.get("end_date"),
        )

        if med_key not in seen_meds:
            merged["medications"].append(med)
            seen_meds.add(med_key)

    return merged


def run_extraction(data_dir: Path, output_path: Path) -> list[dict]:
    synopsis_texts = load_synopsis_texts(data_dir)
    all_results: list[dict] = []

    for idx, clinical_note in enumerate(synopsis_texts, start=1):
        logger.info(f"Processing Synopsis {idx} ...")

        chunks = text_splitter.split_text(clinical_note)

        chunk_outputs = []

        for i, chunk in enumerate(chunks):
            logger.info(f"  → Chunk {i+1}/{len(chunks)}")

            try:
                result = chain.invoke({"clinical_note": chunk})
                clean = result.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean)
                chunk_outputs.append(parsed)

            except json.JSONDecodeError as e:
                logger.error(f"Chunk {i+1} failed JSON parse: {e}")
                continue
            except Exception as e:
                logger.error(f"Chunk {i+1} failed: {e}")
                continue
        final_result = merge_results(chunk_outputs)

        if final_result:
            all_results.append(final_result)


        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)

    return all_results

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")

    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir     = project_root / "Data"
    output_path  = project_root / "output_extractions.json"
    all_results = run_extraction(data_dir, output_path)
    logger.info(f"\n✓ {len(all_results)} total records saved to {output_path}")


if __name__ == "__main__":
    main()

