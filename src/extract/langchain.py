from langchain_community.llms import Ollama
import langchain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage


model = Ollama(model="gemma-local", temperature = 0)

template = 
"""
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
- Return a JSON file where each element represents one medication record.
"""

prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=template), HumanMessage(content="{clinical_notes}")
])

chain = prompt | model | parser

def load_synopsis_texts(data_dir: Path) -> list[str]:
    texts: list[str] = []
    for i in range(1, 11):
        file_path = data_dir / f"Synopsis {i}.txt"
        texts.append(file_path.read_text(encoding="utf-8"))
    return texts


def main():
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "Data"
    synopsis_texts = load_synopsis_texts(data_dir)

    all_results = []

    for idx, clinical_note in enumerate(synopsis_texts, start=1):
        print("=" * 80)
        print(f"Synopsis {idx}")
        print("=" * 80)
        
        result = chain.invoke({"clinical_note": clinical_note})
        all_results.extend(result)
        print(json.dumps(result, indent=2))

    # Save all results to a single JSON file
    output_path = project_root / "output_extractions.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nAll results saved to {output_path}")


if __name__ == "__main__":
    main()

