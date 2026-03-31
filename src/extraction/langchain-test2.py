# Agentic Chunking

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


segmentation_model = OllamaLLM(
    model="gemma-local",
    temperature=0.1,      # small amount of flexibility for boundary reasoning
    num_ctx=4096,
    num_predict=2048,     
    repeat_penalty=1.1,
    timeout=1200,
    seed=42,
    keep_alive=-1,
    num_gpu=1,
    num_thread=8,
    format="json",        
)
# ---------------------------------------------------------------------------
# Output structures
# ---------------------------------------------------------------------------

@dataclass
class AgenticSegment:
    """One condition-focused segment identified by the LLM."""
    index: int
    condition: str        # Condition label given by the LLM
    content: str          # Raw text of this segment
    medication_count: int = 0   # Populated after parsing


@dataclass
class AgenticChunkingResult:
    """Full output of the agentic segmentation pass."""
    segments: list[AgenticSegment]
    raw_llm_output: str           # Original LLM response before parsing
    extraction_input: str         # Final formatted string for extraction pass


# ---------------------------------------------------------------------------
# Segmentation prompt
# ---------------------------------------------------------------------------

SEGMENTATION_SYSTEM = """
You are a clinical text segmentation engine.

Your ONLY job is to read a clinical note and divide it into discrete segments.
Each segment must cover exactly ONE medical condition and ALL medications
associated with that condition.

Rules:
- Patient demographic information (ID, name, age, gender, ethnicity) must appear
  in EVERY segment so each segment is fully self-contained.
- Do NOT summarise, paraphrase, or omit any text. Copy content exactly as written.
- Do NOT merge conditions. One condition = one segment.
- Do NOT invent conditions or medications not present in the note.

Return a JSON array in exactly this format:
[
  {
    "condition": "<condition name>",
    "content": "<patient demographics>\\n<all medications for this condition, copied verbatim>"
  },
  {
    "condition": "<condition name>",
    "content": "<patient demographics>\\n<all medications for this condition, copied verbatim>"
  }
]

Return ONLY the JSON array. No explanation, no markdown, no preamble.
"""

segmentation_prompt = ChatPromptTemplate.from_messages([
    ("system", SEGMENTATION_SYSTEM),
    ("user", "{clinical_note}"),
])

segmentation_chain = segmentation_prompt | segmentation_model


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_segmentation_output(raw: str) -> list[dict]:
    """
    Parse the LLM's JSON array response.
    Handles common model slippage:
      - Markdown code fences around the JSON
      - A single dict returned instead of a list
      - Trailing commas (via lenient fallback)
    """
    clean = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        # Attempt to extract the first [...] block if model added surrounding text
        match = re.search(r"\[.*\]", clean, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
        else:
            raise

    # Model may return a single dict instead of a list — normalise to list
    if isinstance(parsed, dict):
        parsed = [parsed]

    return parsed


def _count_medications(content: str) -> int:
    """Estimate medication count by counting Medication ID occurrences."""
    return len(re.findall(r"Medication ID\s*[:]\s*M\d+", content, re.IGNORECASE))


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------

def agentic_chunk(clinical_note: str) -> AgenticChunkingResult:
    """
    Pass 1 — LLM segments the clinical note into condition-focused blocks.

    Each returned segment is fully self-contained:
      - Patient demographics repeated in every segment
      - All medications for one condition only
      - Content copied verbatim from the original note

    The resulting extraction_input is labelled and ready to pass directly
    to the extraction chain as {clinical_note}.
    """
    logger.info("Agentic segmentation: sending note to segmentation model...")

    raw_output = segmentation_chain.invoke({"clinical_note": clinical_note})
    logger.debug(f"Raw segmentation output:\n{raw_output[:500]}")

    try:
        parsed_segments = _parse_segmentation_output(raw_output)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Segmentation parse failed: {e}\nRaw output: {raw_output[:500]}")
        # Graceful fallback — treat the whole note as one segment
        logger.warning("Falling back to single-segment (full note)")
        fallback_segment = AgenticSegment(
            index=0,
            condition="FULL NOTE",
            content=clinical_note,
            medication_count=_count_medications(clinical_note),
        )
        return AgenticChunkingResult(
            segments=[fallback_segment],
            raw_llm_output=raw_output,
            extraction_input=f"[Segment 1 — FULL NOTE]\n{clinical_note}",
        )

    # Build AgenticSegment objects
    segments: list[AgenticSegment] = []
    for i, seg in enumerate(parsed_segments):
        condition = seg.get("condition", f"Condition {i+1}").strip()
        content = seg.get("content", "").strip()
        if not content:
            logger.warning(f"Segment {i+1} ('{condition}') has empty content — skipping")
            continue
        segments.append(AgenticSegment(
            index=i,
            condition=condition,
            content=content,
            medication_count=_count_medications(content),
        ))

    if not segments:
        logger.error("Segmentation returned no usable segments — falling back to full note")
        fallback_segment = AgenticSegment(
            index=0, condition="FULL NOTE", content=clinical_note,
            medication_count=_count_medications(clinical_note),
        )
        segments = [fallback_segment]

    # Log summary
    logger.info(
        f"Segmentation complete: {len(segments)} segments — "
        + ", ".join(f"'{s.condition}' ({s.medication_count} meds)" for s in segments)
    )

    # Build extraction input — each segment clearly labelled
    extraction_parts = [
        f"[Segment {s.index + 1} — {s.condition}]\n{s.content}"
        for s in segments
    ]
    extraction_input = "\n\n---\n\n".join(extraction_parts)

    return AgenticChunkingResult(
        segments=segments,
        raw_llm_output=raw_output,
        extraction_input=extraction_input,
    )