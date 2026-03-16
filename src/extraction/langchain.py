from langchain_community.llms import Ollama
import langchain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage


model = Ollama(model="gemma-local", temperature = 0)

template = """

You are a helpful assistant for extracting information from a given medical clinical note.
Task: 
    Please extract the following information from the text:


Use exact text spans from the original text. Do not paraphrase.
Return entities in the order they appear.

Example:
            Patient ID: P700. Mr Tan Wei Ming is a 58-year-old Chinese male who was diagnosed with Hypertension on 15 March 2025 after presenting with dizziness.
            The trigger symptom was dizziness.
            He was started on Drug ID 12 – Amlodipine 5mg once daily, 
            with a prescription start date of 15 March 2025, 
            for a duration of 180 days, and an expected end date of 11 September 2025.
"""

prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=template)
]



