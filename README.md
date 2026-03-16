# Knowledge-Graph-Exploration
cd into src
Run 'ollama create gemma-local -f .\Modelfile'
change model_id = gemma-local & model_url = "http://localhost:11434"


Clinical Notes (.txt)
        ↓
LangChain / MedGemma (extraction)
        ↓
JSON output
        ↓
Pydantic validation 
        ↓
Converter (JSON → nodes.csv + edges.csv)
        ↓
AWS Neptune