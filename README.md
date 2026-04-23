# Knowledge-Graph-Exploration
To run the extraction of structured notes:
1. ``cd src/extract``
2. Run ``ollama create gemma-local -f .\Modelfile``
3. Ensure ``model_id = gemma-local`` & ``model_url = "http://localhost:11434"``

# Overall Pipeline
Clinical Notes (.txt) → 
Preprocessing Phase → 
LLM Extraction (LangChain/LangExtract) →
Raw JSON (Flat Entity Extraction) → 
Post Processing  → 
Graph Conversion (Nodes & Edges) →
AWS Neptune KG

## 1. Preprocessing
### Transforms raw clinical notes into structured, clean, and context-preserving inputs to improve the accuracy and reliability of downstream LLM-based extraction
**Text Cleaning**
- White Space Normalization: Remove excessive spaces, normalize line breaks, and trim trailing whitespace
- PHI Marker Removal: Removal of redacted placeholders (e.g., ``[REDACTED]``)

**Section Segmentation**
- Detect and segment clinical notes into structured sections (e.g., Past Medical History, Medications, Examination, Care Plan, et.)

**Chunking**
- Use section-based chunking as the primary strategy
- For large sections (e.g., Past Medical History), further split into logical sub-units (e.g., per condition block)

**Negation Detection**
- Identify negated statements (e.g., “no chest pain”, “denies fever”)
- Store negation flags for use in post-processing to prevent false positive entity extraction 


**_Note_**: Medical Abbreviations and Acronyms (e.g., HTN -> Hypertension) will be handled by MedGemma in the following stage

## 2. LLM Extraction
### Convert text chunks into standardized clinical entities for downstream KG construction.

The following entities are extracted from the clinical notes: \
&emsp; **Patient**: `Patient ID`, `Patient Name`, `Patient Age`, `Patient Gender`, `Patient Ethnicity` . \
&emsp; **Medication & Condition**: `Medication ID`, `Medication Name`, `Medication Start Date`, `Medication End Date`, `Medical Condition(s)` 

**LangChain**   
 - Leverage on Ollama's MedGemma Locally Downloaded Model for entity extraction 
 - Faster processing speed 

**LangExtract**
 - Leverage on Ollama's MedGemma Locally Downloaded Model for entity extraction
 - Slower processing speed


## 3. Post Processing

**Filtering** 
- Negation Filtering

**Normalization**
- Case Normalization: Apply consistent text formatting 
- Data Type Standardization: Ensuring consistent data types (e.g., `Dates` to be formatted to 'DD/MM/YYYY', `age` as integer)

**Clinical Code Mapping (Canonicalization)**
- Map normalized entities to standardized medical ontologies:
  - `Conditions` → ICD-10 or ULMS
  - `Medications` → SNOMED CT or RxNorm


## 4. Graph Conversion 
Transforms the fully post-processed structured JSON into graph-ready CSV files for bulk ingestion into AWS Neptune
- Input: Structured JSON 
- Output: ``nodes.csv``, ``edges.csv``

**Nodes** : \
&emsp;  1. Patient: ``Patient ID`` , ``Patient Name``, ``Patient Age``, ``Patient Gender``, ``Patient Ethnicity`` \
&emsp;  2. Medications: ``Mediation ID``, ``Medication Name`` \
&emsp;  3. Conditions: ``Condition Name`` 
Nodes are deduplicated to ensure uniqueness across dataset??

**Edges**: \
&emsp;  1. Patient —> Condition: ``Patient — IS_DIAGONSED_WITH —> Condition`` \
&emsp;  2. Patient —> Medication:``Patient — IS_PRESCRIBED —> Medication [start_date, end_date] `` \
&emsp;  3. Medication —> Condition:``Medication — TREATS —> Condition`` \
&emsp;  4. Patient Property:``Patient — HAS_ETHNICITY —> Ethnicity`` \
&emsp;  5. Patient Property:``Patient — HAS_GENDER —> Male`` 
