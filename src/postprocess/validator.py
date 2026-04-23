import json
import re
import hashlib
from pathlib import Path
from datetime import datetime, date
from typing import Any
from pydantic import ValidationError

from schema import PatientRecord

def load_json(input_path: str | Path) -> list[dict]:
    input_path = Path(input_path)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data

    raise ValueError("Input JSON must be a dict or list of dicts.")


def clean_text(value: object | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_gender(value: object | None) -> str | None:
    v = clean_text(value).lower()
    mapping = {
        "m": "Male",
        "f": "Female",
        "male": "Male",
        "female": "Female",
        "man": "Male",
        "woman": "Female",
    }
    return mapping.get(v, clean_text(value).title() if v else None)


def normalize_ethnicity(value: object | None) -> str | None:
    v = clean_text(value)
    return v.title() if v else None


def normalize_age(value: object | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def normalize_date(value: object | None) -> date | None:
    v = clean_text(value)
    if not v:
        return None

    possible_input_formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%b %d %Y",
        "%B %d %Y",
        "%d %b %Y",
        "%d %B %Y",
    ]

    for input_format in possible_input_formats:
        try:
            parsed_date = datetime.strptime(v, input_format).date()
            return parsed_date.strftime("%d/%m/%Y")
        except ValueError:
            pass

    return None


def make_patient_id(name: str, age: Any, gender: str) -> str:
    raw = f"{name}|{age}|{gender}"
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:10]
    return f"P_{digest}"


def make_medication_id(name: str) -> str:
    base = clean_text(name).upper()
    base = re.sub(r"[^A-Z0-9]+", "_", base).strip("_")
    if not base:
        base = "UNKNOWN_MED"
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()[:6]
    return f"M_{base}_{digest}"


def normalize_medication(med: dict) -> dict | None:
    med_name = clean_text(
        med.get("medication_name")
        or med.get("med_name")
        or med.get("name")
        or med.get("drug")
    )

    condition = clean_text(
        med.get("condition")
        or med.get("diagnosis")
        or med.get("indication")
    )

    start_date = normalize_date(med.get("start_date"))
    end_date = normalize_date(med.get("end_date"))

    medication_id = clean_text(med.get("medication_id"))
    if not medication_id and med_name:
        medication_id = make_medication_id(med_name)

    # Drop rows that are too empty to be useful
    if not med_name:
        return None

    return {
        "medication_id": medication_id,
        "medication_name": med_name,
        "condition": condition if condition else "Unknown",
        "start_date": start_date,
        "end_date": end_date,
    }


def dedupe_medications(medications: list[dict]) -> list[dict]:
    seen = set()
    output = []

    for med in medications:
        key = (
            med["medication_id"],
            med["medication_name"].lower(),
            med["condition"].lower(),
            med["start_date"],
            med["end_date"],
        )
        if key not in seen:
            seen.add(key)
            output.append(med)

    return output


def normalize_record(record: dict) -> dict:
    patient_name = clean_text(
        record.get("patient_name")
        or record.get("name")
        or record.get("patient")
    )

    patient_age = normalize_age(
        record.get("patient_age")
        or record.get("age")
    )

    patient_gender = normalize_gender(
        record.get("patient_gender")
        or record.get("gender")
    )

    patient_ethnicity = normalize_ethnicity(
        record.get("patient_ethnicity")
        or record.get("ethnicity")
        or record.get("race")
    )

    patient_id = clean_text(record.get("patient_id"))
    if not patient_id:
        patient_id = make_patient_id(patient_name, patient_age, patient_gender)

    raw_meds = record.get("medications", [])
    if not isinstance(raw_meds, list):
        raw_meds = []

    medications = []
    for med in raw_meds:
        if isinstance(med, dict):
            normalized = normalize_medication(med)
            if normalized:
                medications.append(normalized)

    medications = dedupe_medications(medications)

    return {
        "patient_id": patient_id,
        "patient_name": patient_name if patient_name else "Unknown",
        "patient_age": patient_age,
        "patient_gender": patient_gender,
        "patient_ethnicity": patient_ethnicity,
        "medications": medications,
    }


def load_and_postprocess(input_path: str | Path) -> list[PatientRecord]:
    raw_records = load_json(input_path)

    valid_records: list[PatientRecord] = []
    failed = 0

    for i, raw in enumerate(raw_records):
        try:
            cleaned = normalize_record(raw)
            validated = PatientRecord(**cleaned)
            valid_records.append(validated)
        except ValidationError as e:
            failed += 1
            print(f"[Record {i}] Validation failed:\n{e}\n")

    print(f"{len(valid_records)}/{len(raw_records)} records passed post-processing + validation")
    if failed:
        print(f"{failed} records failed")

    return valid_records


def save_output(records: list[PatientRecord], output_path: str | Path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    serializable = [r.model_dump() for r in records]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)

    print(f"Saved cleaned output to {output_path}")

def run_postprocessing(input_dir: Path, output_dir: Path):

    for input_file in sorted(input_dir.glob("*.json")):
        output_file = output_dir / input_file.name
        print(f"Post Processing {input_file} -> {output_file}")
        records = load_and_postprocess(input_file)
        save_output(records, output_file)

if __name__ == "__main__":
    run_postprocessing()
    # run_postprocessing(
    #     project_root / "outputs" / "extracted_entities",
    #     project_root / "outputs" / "postprocessed_entities"
    # )