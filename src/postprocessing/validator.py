
import json
from pathlib import Path
from pydantic import ValidationError
from schema import ExtractionRecord


def load_and_validate(input_path: str | Path) -> list[ExtractionRecord]:
    """
    Load a JSON file and validate each record against ExtractionRecord.
    Skips invalid records with a warning instead of crashing.
    Returns a list of validated ExtractionRecord objects.
    """
    input_path = Path(input_path)

    print(f"\nLoading {input_path} ...")
    with open(input_path, encoding="utf-8") as f:
        raw = json.load(f)

    records: list[ExtractionRecord] = []
    for i, item in enumerate(raw):
        try:
            records.append(ExtractionRecord(**item))
        except ValidationError as e:
            print(f"  ⚠ Skipping record {i} (validation error):\n{e}\n")

    print(f"  {len(records)}/{len(raw)} records passed validation\n")
    return records


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate extraction JSON against schema")
    parser.add_argument("--input", required=True, help="Path to output_extractions.json")
    args = parser.parse_args()

    records = load_and_validate(args.input)
    print(f"Validation complete. {len(records)} valid records ready for conversion.")