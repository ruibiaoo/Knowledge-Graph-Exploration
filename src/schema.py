from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# =========================
# Node Models
# =========================

class PatientNode(BaseModel):
    id: str = Field(description="Unique patient identifier, e.g., 'P84271'")
    name: str = Field(description="Full name of the patient")
    age: int = Field(description="Age in years")
    gender: str = Field(description="Gender of patient, e.g., 'Male', 'Female'")
    ethnicity: str = Field(description="Ethnicity, e.g., 'Chinese', 'Malay', 'Indian'")


class MedicationNode(BaseModel):
    id: str = Field(description="Unique medication identifier, e.g., 'M228'")
    name: str = Field(description="Medication name, e.g., 'Metformin'")


class ConditionNode(BaseModel):
    name: str = Field(description="Full condition name, e.g., 'Type 2 Diabetes Mellitus'")


class EthnicityNode(BaseModel):
    name: str = Field(description="Ethnicity name, e.g., 'Malay'")


class GenderNode(BaseModel):
    name: str = Field(description="Gender name, e.g., 'Male'")


# =========================
# Edge Models
# =========================

class PrescribedEdge(BaseModel):
    patient_id: str = Field(description="Patient ID")
    medication_id: str = Field(description="Medication ID")
    start_date: str = Field(description="Start date (DD/MM/YYYY)")
    end_date: str = Field(description="End date (DD/MM/YYYY)")


class DiagnosedWithEdge(BaseModel):
    patient_id: str = Field(description="Patient ID")
    condition_name: str = Field(description="Condition name")


class TreatedWithEdge(BaseModel):
    medication_id: str = Field(description="Medication ID")
    condition_name: str = Field(description="Condition name")


class HasEthnicityEdge(BaseModel):
    patient_id: str = Field(description="Patient ID")
    ethnicity: str = Field(description="Ethnicity")


class HasGenderEdge(BaseModel):
    patient_id: str = Field(description="Patient ID")
    gender: str = Field(description="Gender")


# Medication Record Model
class MedicationRecord(BaseModel):
    medication_id: str
    medication_name: str
    condition: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

# Patient Record Model 
class PatientRecord(BaseModel):
    patient_id: str
    patient_name: str
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    patient_ethnicity: Optional[str] = None
    medications: List[MedicationRecord] = Field(default_factory=list)



# =========================
# Final Container Model
# =========================

class GraphSchema(BaseModel):

    # Nodes
    patient_nodes: List[PatientNode] = Field(description="Exactly one patient node")
    medication_nodes: List[MedicationNode] = Field(description="All medications")
    condition_nodes: List[ConditionNode] = Field(description="All conditions")
    ethnicity_nodes: List[EthnicityNode] = Field(description="All ethnicities")
    gender_nodes: List[GenderNode] = Field(description="All genders")

    # Edges
    prescribed_edges: List[PrescribedEdge] = Field(description="Patient → Medication with dates")
    diagnosed_edges: List[DiagnosedWithEdge] = Field(description="Patient → Condition")
    treats_edges: List[TreatedWithEdge] = Field(description="Medication → Condition")
    ethnicity_edges: List[HasEthnicityEdge] = Field(description="Patient → Ethnicity")
    gender_edges: List[HasGenderEdge] = Field(description="Patient → Gender")

    # Metadata
    confidence: int = Field(ge=1, le=7, description="Confidence score")