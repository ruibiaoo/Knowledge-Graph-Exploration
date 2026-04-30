from pathlib import Path

from preprocess.preprocess_txt import preprocess_notes_txt
from preprocess.preprocess_json import preprocess_notes_json
from extraction.langextract import run_extraction
from postprocess.validator import run_postprocessing
from convert.converter import run_conversion

def main():
    project_root = Path(__file__).resolve().parent.parent

    data_dir = project_root / "Data"                                         # Original notes stored here
    preprocessed_dir = project_root / "outputs" / "preprocessed_notes"       # Preprocess notes stored here
    extracted_dir = project_root / "outputs" / "extracted_entities"          # Extracted entities stored here
    postprocessed_dir = project_root / "outputs" / "postprocessed_entities"  # Postprocessed entities stored here
    graph_dir = project_root / "outputs" / "graph_csv"                       # Final graph CSVs stored here

    preprocessed_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir.mkdir(parents=True, exist_ok=True)
    postprocessed_dir.mkdir(parents=True, exist_ok=True)
    graph_dir.mkdir(parents=True, exist_ok=True)

    print("\n🚀 Starting Clinical Pipeline...\n")

    # 1. Preprocessing
    print("Step 1: Preprocessing")
    preprocess_notes_txt(data_dir, preprocessed_dir)
    preprocess_notes_json(data_dir, preprocessed_dir)

    # 2. Extraction
    print("Step 2: LLM Extraction")
    run_extraction(preprocessed_dir, extracted_dir)

    # 3. Post-processing
    print("Step 3: Post-processing")
    run_postprocessing(extracted_dir, postprocessed_dir)

    # 4. Conversion
    print("Step 4: Graph Conversion")
    run_conversion(postprocessed_dir, graph_dir)

    print("\n Pipeline completed!\n")

if __name__ == "__main__":
    main()