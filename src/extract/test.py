import langextract as lx
import textwrap
from pathlib import Path
import json

# ==============================
# PROMPT (SIMPLIFIED)
# ==============================

prompt = textwrap.dedent("""
You are a precise clinical data extraction engine. Your task is to extract specific information **ONLY** from the provided Clinical Notes.
                         
**Task:**
Extract *ALL* of the following information **ONLY** from the given Clinical Notes
    1. Patient ID 
    2. Patient Full Name 
    3. Patient Age 
    4. Patient Gender 
    5. Patient Ethnicity 
    For **EACH** medication
    6. Medication ID prescribed to patient 
    7. Medication Name prescribed to patient 
    8. Start Date of medication course 
    9. End Date of medication course 
    10. Medical Condition(s) patient suffered from

**Extraction Guidelines:**
- **Dates**: Standardize all dates to the format DD/MM/YYYY. 
- Dates must be DD/MM/YYYY
""")

# ==============================
# REMOVE EXAMPLES (MAJOR SPEED BOOST)
# ==============================

examples = []


# ==============================
# TEXT LOADING
# ==============================

def load_synopsis_texts(data_dir: Path) -> list[str]:
    texts: list[str] = []
    for i in range(1, 11):
        file_path = data_dir / f"Synopsis {i}.txt"
        texts.append(file_path.read_text(encoding="utf-8"))
    return texts


# ==============================
# CHUNKING (CRITICAL FOR LONG TEXT)
# ==============================

def chunk_text(text, chunk_size=1000, overlap=100):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


# ==============================
# DEDUPLICATION
# ==============================

def deduplicate(extractions):
    seen = set()
    unique = []

    for e in extractions:
        key = (e.extraction_class, e.extraction_text)

        if key not in seen:
            seen.add(key)
            unique.append(e)

    return unique


# ==============================
# JSON CONVERSION
# ==============================

def convert_to_json(extractions):
    structured = []

    for e in extractions:
        item = {
            "class": e.extraction_class,
            "text": e.extraction_text,
        }

        if e.attributes:
            item["attributes"] = e.attributes

        structured.append(item)

    return structured


# ==============================
# MAIN PIPELINE
# ==============================

def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "Data"
    output_dir = project_root / "outputs"
    output_dir.mkdir(exist_ok=True)

    synopsis_texts = load_synopsis_texts(data_dir)

    for idx, input_text in enumerate(synopsis_texts, start=1):
        print("=" * 80)
        print(f"Synopsis {idx}")
        print("=" * 80)

        # 🔥 CHUNK THE INPUT
        chunks = chunk_text(input_text)

        all_extractions = []

        for chunk_idx, chunk in enumerate(chunks):
            print(f"Processing chunk {chunk_idx + 1}/{len(chunks)}...")

            result = lx.extract(
                text_or_documents=chunk,
                prompt_description=prompt,
                examples=examples,  
                model_id="gemma-local",
                model_url="http://localhost:11434",
                fence_output=False,
                use_schema_constraints=True, 
            )

            all_extractions.extend(result.extractions)

        # 🔥 DEDUPLICATE AFTER MERGING CHUNKS
        all_extractions = deduplicate(all_extractions)

        print("\nExtracted entities:\n")
        print(all_extractions)

        structured_output = convert_to_json(all_extractions)

        output_file = output_dir / f"synopsis_{idx}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(structured_output, f, indent=2)

        print(f"\nSaved JSON to {output_file}\n")


# ==============================
# ENTRY
# ==============================

if __name__ == "__main__":
    main()