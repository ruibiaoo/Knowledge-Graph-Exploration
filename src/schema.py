from pydantic import BaseModel, Field
from typing import Optional

# Node Models 
class PatientNode(BaseModel):
    patient_id: str                  
    name: str                         
    age: int                           
    gender: str                        
    ethnicity: str                     

class ConditionNode(BaseModel):
    condition_id: str                  
    name: str                         

class MedicationNode(BaseModel):
    medication_id: str                 
    name: str                         
    dosage: str                       

#Edge Models
class PrescribedEdge(BaseModel):
    patient_id: str                   
    medication_id: str
    start_date: str
    end_date: str

class HasConditionEdge(BaseModel):
    patient_id: str                   
    condition_id: str                    

class TreatsEdge(BaseModel):
    medication_id: str                
    condition_id: str                  

# ── Top-level extraction result (one record per med) ──────

class ExtractionRecord(BaseModel):
    patient_id: str
    patient_name: str
    age: int
    gender: str
    ethnicity: str
    medication_id: str
    medication_name_dosage: str
    start_date: str
    end_date: str
    condition: str