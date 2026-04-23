import json
import csv
import re

from pathlib import Path
from schema import *


def normalize_condition(name: str) -> str:
    return re.sub(r"\s+", "_", name.strip().upper())

# Load post-processed JSON data
def load_json_file(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Conversion to graph format
def convert(data: list[dict]):

    patients = {}
    medications = {}
    conditions = {}
    ethnicities = {}
    genders = {}

    prescribed_edges = []
    diagnosed_edges = []
    treats_edges = []
    ethnicity_edges = []
    gender_edges = []

    seen_prescribed = set()
    seen_diag = set()
    seen_treats = set()

    for record in data:

        # Patient Node
        p = PatientNode(
            id=record["patient_id"],
            name=record["patient_name"],
            age=record["patient_age"],
            gender=record["patient_gender"],
            ethnicity=record["patient_ethnicity"]
        )
        patients[p.id] = p

        # Ethnicity + Gender Nodes
        ethnicities[p.ethnicity] = EthnicityNode(name=p.ethnicity)
        genders[p.gender] = GenderNode(name=p.gender)

        ethnicity_edges.append(HasEthnicityEdge(
            patient_id=p.id,
            ethnicity=p.ethnicity
        ))

        gender_edges.append(HasGenderEdge(
            patient_id=p.id,
            gender=p.gender
        ))

        # Medications + Conditions Nodes
        for med in record["medications"]:

            # Medication Node
            m = MedicationNode(
                id=med["medication_id"],
                name=med["medication_name"]
            )
            medications[m.id] = m

            # Condition Node
            cond_name = med["condition"]
            cond_id = normalize_condition(cond_name)

            c = ConditionNode(name=cond_name)
            conditions[cond_id] = c

            # =========================
            # Edges
            # =========================

            # PRESCRIBED Edge
            key = (p.id, m.id, med["start_date"], med["end_date"])
            if key not in seen_prescribed:
                seen_prescribed.add(key)
                prescribed_edges.append(PrescribedEdge(
                    patient_id=p.id,
                    medication_id=m.id,
                    start_date=med["start_date"],
                    end_date=med["end_date"]
                ))

            # DIAGNOSED Edge
            key = (p.id, cond_id)
            if key not in seen_diag:
                seen_diag.add(key)
                diagnosed_edges.append(DiagnosedWithEdge(
                    patient_id=p.id,
                    condition_name=cond_name
                ))

            # TREATS Edge
            key = (m.id, cond_id)
            if key not in seen_treats:
                seen_treats.add(key)
                treats_edges.append(TreatedWithEdge(
                    medication_id=m.id,
                    condition_name=cond_name
                ))

    return {
        "patient_nodes": list(patients.values()),
        "medication_nodes": list(medications.values()),
        "condition_nodes": list(conditions.values()),
        "ethnicity_nodes": list(ethnicities.values()),
        "gender_nodes": list(genders.values()),
        "prescribed_edges": prescribed_edges,
        "diagnosed_edges": diagnosed_edges,
        "treats_edges": treats_edges,
        "ethnicity_edges": ethnicity_edges,
        "gender_edges": gender_edges,
    }



# CSV Writers
def write_nodes_csv(graph, output_file: Path):

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["~id", "~label", "name", "age", "gender", "ethnicity"])

        for n in graph["patient_nodes"]:
            writer.writerow([n.id, "Patient", n.name, n.age, n.gender, n.ethnicity])

        for n in graph["medication_nodes"]:
            writer.writerow([n.id, "Medication", n.name, "", "", ""])

        for n in graph["condition_nodes"]:
            writer.writerow([normalize_condition(n.name), "Condition", n.name, "", "", ""])

        for n in graph["ethnicity_nodes"]:
            writer.writerow([n.name.upper(), "Ethnicity", n.name, "", "", ""])

        for n in graph["gender_nodes"]:
            writer.writerow([n.name.upper(), "Gender", n.name, "", "", ""])


def write_edges_csv(graph, output_file: Path):

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["~id", "~from", "~to", "~label", "start_date", "end_date"])

        eid = 1

        for e in graph["prescribed_edges"]:
            writer.writerow([f"e{eid}", e.patient_id, e.medication_id, "IS_PRESCRIBED", e.start_date, e.end_date])
            eid += 1

        for e in graph["diagnosed_edges"]:
            writer.writerow([f"e{eid}", e.patient_id, normalize_condition(e.condition_name), "IS_DIAGNOSED_WITH", "", ""])
            eid += 1

        for e in graph["treats_edges"]:
            writer.writerow([f"e{eid}", e.medication_id, normalize_condition(e.condition_name), "IS_TREATED_WITH", "", ""])
            eid += 1

        for e in graph["ethnicity_edges"]:
            writer.writerow([f"e{eid}", e.patient_id, e.ethnicity.upper(), "HAS_ETHNICITY", "", ""])
            eid += 1

        for e in graph["gender_edges"]:
            writer.writerow([f"e{eid}", e.patient_id, e.gender.upper(), "HAS_GENDER", "", ""])
            eid += 1


def run_conversion(input_path: Path, output_dir: Path):

    all_records = []

    if input_path.is_file():
        data = load_json_file(input_path)
        if isinstance(data, list):
            all_records.extend(data)
        elif isinstance(data, dict):
            all_records.append(data)

    elif input_path.is_dir():
        json_files = sorted(input_path.glob("*.json"))
        for json_file in json_files:
            data = load_json_file(json_file)
            if isinstance(data, list):
                all_records.extend(data)
            elif isinstance(data, dict):
                all_records.append(data)

    graph = convert(all_records)

    write_nodes_csv(graph, output_dir / "nodes.csv")
    write_edges_csv(graph, output_dir / "edges.csv")


if __name__ == "__main__":
    run_conversion()
    # project_root = Path(__file__).resolve().parents[2]
    # run_conversion(
    #     project_root / "outputs" / "postprocessed_entities",
    #     project_root / "outputs" / "graph_csv"
    # )