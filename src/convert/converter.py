import csv
import re
import argparse
from pathlib import Path

from schema import *
from validator import load_and_validate

def make_condition_id(condition_name: str) -> str:
    """
    Derive a short stable ID from a condition name.
    e.g. "Type 2 Diabetes Mellitus" → "TYPE_2_DIABETES_MELLITUS"
    """
    return re.sub(r"\s+", "_", condition_name.strip().upper())


def split_medication(medication_name_dosage: str) -> tuple[str, str]:
    """
    Split "Metformin 850mg" → ("Metformin", "850mg")
    Falls back to (full_string, "") if no dosage token found.
    """
    parts = medication_name_dosage.rsplit(" ", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return medication_name_dosage, ""


# ── Core converter ────────────────────────────────────────────────────────────

def convert(records: list[ExtractionRecord]) -> tuple[
    dict[str, PatientNode],
    dict[str, ConditionNode],
    dict[str, MedicationNode],
    list[PrescribedEdge],
    list[HasConditionEdge],
    list[TreatsEdge],
]:
    """
    Deduplicate nodes and build edge lists from validated ExtractionRecords.
    Returns dicts keyed by ID for nodes, and plain lists for edges.
    """
    patients:    dict[str, PatientNode]    = {}
    conditions:  dict[str, ConditionNode]  = {}
    medications: dict[str, MedicationNode] = {}

    prescribed_edges:    list[PrescribedEdge]   = []
    has_condition_edges: list[HasConditionEdge] = []
    treats_edges:        list[TreatsEdge]       = []

    # Track edges already added to avoid duplicates
    seen_prescribed:    set[tuple] = set()
    seen_has_condition: set[tuple] = set()
    seen_treats:        set[tuple] = set()

    for rec in records:

        # ── Patient node ──────────────────────────────────────────────────────
        if rec.patient_id not in patients:
            patients[rec.patient_id] = PatientNode(
                patient_id=rec.patient_id,
                name=rec.patient_name,
                age=rec.age,
                gender=rec.gender,
                ethnicity=rec.ethnicity,
            )

        # ── Condition node ────────────────────────────────────────────────────
        condition_id = make_condition_id(rec.condition)
        if condition_id not in conditions:
            conditions[condition_id] = ConditionNode(
                condition_id=condition_id,
                name=rec.condition,
            )

        # ── Medication node ───────────────────────────────────────────────────
        if rec.medication_id not in medications:
            med_name, dosage = split_medication(rec.medication_name_dosage)
            medications[rec.medication_id] = MedicationNode(
                medication_id=rec.medication_id,
                name=med_name,
                dosage=dosage,
            )

        # ── PRESCRIBED edge  (Patient → Medication) ───────────────────────────
        prescribed_key = (rec.patient_id, rec.medication_id)
        if prescribed_key not in seen_prescribed:
            seen_prescribed.add(prescribed_key)
            prescribed_edges.append(PrescribedEdge(
                patient_id=rec.patient_id,
                medication_id=rec.medication_id,
                start_date=rec.start_date,
                end_date=rec.end_date,
            ))

        # ── HAS_CONDITION edge  (Patient → Condition) ─────────────────────────
        hc_key = (rec.patient_id, condition_id)
        if hc_key not in seen_has_condition:
            seen_has_condition.add(hc_key)
            has_condition_edges.append(HasConditionEdge(
                patient_id=rec.patient_id,
                condition_id=condition_id,
            ))

        # ── TREATS edge  (Medication → Condition) ─────────────────────────────
        treats_key = (rec.medication_id, condition_id)
        if treats_key not in seen_treats:
            seen_treats.add(treats_key)
            treats_edges.append(TreatsEdge(
                medication_id=rec.medication_id,
                condition_id=condition_id,
            ))

    return patients, conditions, medications, prescribed_edges, has_condition_edges, treats_edges


# ── CSV writers ───────────────────────────────────────────────────────────────

def write_nodes_csv(
    output_path: Path,
    patients:    dict[str, PatientNode],
    conditions:  dict[str, ConditionNode],
    medications: dict[str, MedicationNode],
) -> None:
    """
    Neptune nodes CSV format:
    ~id, ~label, property:Type, ...
    """
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            "~id", "~label",
            "patient_id:String", "name:String", "age:Int", "gender:String", "ethnicity:String",
            "condition_id:String",
            "medication_id:String", "dosage:String",
        ])

        # Patient rows
        for p in patients.values():
            writer.writerow([
                p.patient_id, "Patient",
                p.patient_id, p.name, p.age, p.gender, p.ethnicity,
                "", "", "",
            ])

        # Condition rows
        for c in conditions.values():
            writer.writerow([
                c.condition_id, "Condition",
                "", c.name, "", "", "",
                c.condition_id,
                "", "",
            ])

        # Medication rows
        for m in medications.values():
            writer.writerow([
                m.medication_id, "Medication",
                "", m.name, "", "", "",
                "",
                m.medication_id, m.dosage,
            ])

    print(f"  ✓ nodes.csv  → {output_path}  "
          f"({len(patients)} patients, {len(conditions)} conditions, {len(medications)} medications)")


def write_edges_csv(
    output_path:   Path,
    prescribed:    list[PrescribedEdge],
    has_condition: list[HasConditionEdge],
    treats:        list[TreatsEdge],
) -> None:
    """
    Neptune edges CSV format:
    ~id, ~from, ~to, ~label, property:Type, ...
    """
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            "~id", "~from", "~to", "~label",
            "start_date:String", "end_date:String",
        ])

        edge_id = 1

        # PRESCRIBED  (Patient → Medication)
        for e in prescribed:
            writer.writerow([
                f"e{edge_id}", e.patient_id, e.medication_id, "PRESCRIBED",
                e.start_date, e.end_date,
            ])
            edge_id += 1

        # HAS_CONDITION  (Patient → Condition)
        for e in has_condition:
            writer.writerow([
                f"e{edge_id}", e.patient_id, e.condition_id, "HAS_CONDITION",
                "", "",
            ])
            edge_id += 1

        # TREATS  (Medication → Condition)
        for e in treats:
            writer.writerow([
                f"e{edge_id}", e.medication_id, e.condition_id, "TREATS",
                "", "",
            ])
            edge_id += 1

    print(f"  ✓ edges.csv  → {output_path}  "
          f"({len(prescribed)} PRESCRIBED, {len(has_condition)} HAS_CONDITION, {len(treats)} TREATS)")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Convert extraction JSON to Neptune CSVs")
    parser.add_argument("--input",  required=True, help="Path to output_extractions.json")
    parser.add_argument("--outdir", default="./neptune_load", help="Output directory for CSVs")
    args = parser.parse_args()

    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Validate ──────────────────────────────────────────────────────
    records = load_and_validate(args.input)

    if not records:
        print("No valid records found. Exiting.")
        return

    # ── Step 2: Convert ───────────────────────────────────────────────────────
    patients, conditions, medications, prescribed, has_condition, treats = convert(records)

    write_nodes_csv(out_dir / "nodes.csv", patients, conditions, medications)
    write_edges_csv(out_dir / "edges.csv", prescribed, has_condition, treats)

    print(f"\nDone. Files saved to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()