from pathlib import Path
import logging

# from preprocessing.preprocessing import preprocess_notes
# from extraction import run_extraction
# from postprocess.validator import run_postprocessing
from convert.converter import run_conversion


logging.basicConfig(level=logging.INFO)


def main():

    project_root = Path(__file__).resolve().parent.parent

    data_dir = project_root / "Data"
    raw_output = project_root / "outputs" / "raw_extractions"
    processed_output = project_root / "outputs" / "processed_extractions"
    graph_dir = project_root / "outputs" / "graph_csv"

    print("\n🚀 Starting Clinical Pipeline...\n")

    # 1. Preprocessing
    print("Step 1: Preprocessing")
    preprocess_notes(data_dir)

    # 2. Extraction
    print("Step 2: LLM Extraction")
    run_extraction(data_dir, raw_output)

    # 3. Post-processing
    print("Step 3: Post-processing")
    run_postprocessing(raw_output, processed_output)

    # 4. Conversion
    print("Step 4: Graph Conversion")
    run_conversion(processed_output, graph_dir)

    print("\n Pipeline completed!\n")


if __name__ == "__main__":
    main()