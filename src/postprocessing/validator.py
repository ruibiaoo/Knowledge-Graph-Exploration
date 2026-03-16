
import json
from pathlib import Path
from pydantic import ValidationError
from schema import ExtractionRecord
import argparse

def load_and_validate(input_path: str | Path) -> list[ExtractionRecord]:
    input_path = Path(input_path)

    with open(input_path, encoding="utf-8") as f:
        raw = json.load(f)

    records: list[ExtractionRecord] = []
    for i, item in enumerate(raw):
        records.append(ExtractionRecord(**item))

    print(f"  {len(records)}/{len(raw)} records passed validation\n")
    return records


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Validate extraction JSON against schema")
    parser.add_argument("--input", required=True, help="Path to output_extractions.json")
    args = parser.parse_args()

    records = load_and_validate(args.input)
    print(f"Validation complete. {len(records)} valid records ready for conversion.")