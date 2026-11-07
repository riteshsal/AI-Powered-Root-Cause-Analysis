from typing import TypedDict, Any

from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from dotenv import load_dotenv

import os

load_dotenv()


# 1. RCA State

class RCAState(TypedDict, total=False):
    source_text: str
    incident: dict[str, Any]
    evidence: list[dict[str, Any]]
    five_whys: list[dict[str, Any]]
    root_causes: list[dict[str, Any]]
    missing_evidence: list[dict[str, Any]]
    capa: list[dict[str, Any]]


# -----------------------------
# 2. Groq LLM
# -----------------------------

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=GROQ_API_KEY,
)

# -----------------------------
# 3. Incident Extraction
# -----------------------------

def extract_incident(state: RCAState):
    prompt = f"""
You are a pharmaceutical quality investigation assistant.

Extract the incident information from the text below.

Return ONLY valid JSON with these fields:

{{
    "product_name": "",
    "batch_number": "",
    "incident_type": "",
    "incident_date": "",
    "process_step": "",
    "description": "",
    "observed_result": "",
    "specification": ""
}}

Rules:
- Use only information explicitly present in the text.
- Do not invent missing information.
- If information is missing, return an empty string.
- Do not identify or assume a root cause.
- Keep the information factual.

Investigation text:
{state["source_text"]}
"""

    response = llm.invoke(prompt)

    return {
        "incident": response.content
    }

def analyze_evidence(state: RCAState):
    prompt = f"""
You are a pharmaceutical quality investigation assistant.

Analyze the investigation text and identify factual evidence.

Return ONLY valid JSON in this format:

{{
    "evidence": [
        {{
            "evidence_text": "",
            "source": "",
            "confidence": "High"
        }}
    ]
}}

Rules:
- Include only facts explicitly supported by the investigation text.
- Do not invent evidence.
- Do not identify a root cause.
- Do not convert assumptions into facts.
- Confidence must be High, Medium, or Low.
- "source" should describe where the evidence came from,
  such as investigation document, operator statement, batch result, etc.
- Separate important facts into individual evidence items.

Investigation text:
{state["source_text"]}
"""

    response = llm.invoke(prompt)

    return {
        "evidence": response.content
    }

def five_whys(state: RCAState):
    prompt = f"""
You are a pharmaceutical quality investigation assistant.

Perform a 5 Whys analysis for the incident using only the
investigation text and identified evidence.

Return ONLY valid JSON in this format:

{{
    "five_whys": [
        {{
            "why_number": 1,
            "question": "",
            "answer": "",
            "evidence": "",
            "status": "Supported"
        }}
    ]
}}

Rules:
- Start with the actual problem observed in the investigation.
- Each why should logically follow from the previous answer.
- Use only information explicitly supported by the investigation text
  or evidence.
- Do not invent facts or assumptions.
- If there is not enough evidence to answer a why, write
  "Evidence required" in the answer.
- Do not declare a root cause.
- Status must be either "Supported" or "Evidence Required".
- Include supporting evidence for each answer.

Investigation text:
{state["source_text"]}

Identified evidence:
{state["evidence"]}
"""

    response = llm.invoke(prompt)

    return {
        "five_whys": response.content
    }

def identify_root_causes(state: RCAState):
    prompt = f"""
You are a pharmaceutical quality investigation assistant.

Identify potential root causes and contributing factors based ONLY
on the investigation text, identified evidence, and 5 Whys analysis.

Return ONLY valid JSON in this format:

{{
    "root_causes": [
        {{
            "cause": "",
            "category": "",
            "supporting_evidence": "",
            "confidence": "Medium",
            "status": "Pending Review"
        }}
    ]
}}

Rules:
- These are ONLY potential causes for qualified quality personnel
  to review.
- Never state that a root cause is confirmed.
- Do not convert a possibility, assumption, or correlation into a fact.
- Every potential cause must have supporting evidence.
- If the evidence only suggests a possibility, clearly use words such as
  "may", "possible", or "potential" in the cause.
- Do not infer training deficiencies unless training evidence is available.
- Do not infer equipment failure unless equipment evidence is available.
- Do not infer SOP deficiencies unless the SOP has been reviewed.
- Do not infer operator error beyond what the operator statement explicitly says.
- Do not invent facts, measurements, dates, procedures, or events.
- If there is insufficient evidence for a potential cause, do not include it.
- Possible categories include:
  "Equipment",
  "Process",
  "People",
  "Measurement",
  "Training",
  "Documentation",
  "Environment",
  "Other".
- Confidence must be High, Medium, or Low.
- Status must always be "Pending Review".
- Include the exact investigation evidence that supports each suggestion.

Investigation text:
{state["source_text"]}

Identified evidence:
{state["evidence"]}

5 Whys analysis:
{state["five_whys"]}
"""

    response = llm.invoke(prompt)

    return {
        "root_causes": response.content
    }

def identify_missing_evidence(state: RCAState):
    prompt = f"""
You are a pharmaceutical quality investigation assistant.

Identify evidence that is missing or should be obtained to properly
investigate and confirm the potential root causes.

Return ONLY valid JSON in this format:

{{
    "missing_evidence": [
        {{
            "evidence_required": "",
            "reason": "",
            "status": "Required"
        }}
    ]
}}

Rules:
- Identify only evidence that would be useful for confirming or
  rejecting potential root causes.
- Do not invent evidence.
- Do not assume that missing evidence exists.
- Do not declare a root cause.
- Focus on practical investigation evidence.
- Status must be "Required" or "Available".
- If no important evidence is missing, return an empty list.

Investigation text:
{state["source_text"]}

Identified evidence:
{state["evidence"]}

5 Whys analysis:
{state["five_whys"]}

Potential root causes:
{state["root_causes"]}
"""

    response = llm.invoke(prompt)

    return {
        "missing_evidence": response.content
    }


def recommend_capa(state: RCAState):
    prompt = f"""
You are a pharmaceutical quality investigation assistant.

Recommend potential CAPA actions based on the investigation,
evidence, 5 Whys analysis, potential root causes, and missing evidence.

Return ONLY valid JSON in this format:

{{
    "capa": [
        {{
            "action_type": "Corrective",
            "action": "",
            "reason": "",
            "effectiveness_check": "",
            "status": "Proposed",
            "owner": "",
            "due_date": ""
        }}
    ]
}}

Rules:
- CAPA actions are recommendations for qualified quality personnel.
- Do not treat potential root causes as confirmed root causes.
- Every action must be connected to an identified problem,
  potential cause, or missing evidence.
- Do not invent specific frequencies, time periods, batch counts,
  acceptance limits, owners, due dates, or procedural requirements.
- Do not invent completed actions.
- If a specific frequency, limit, owner, or due date is not provided
  in the investigation, leave it unspecified.
- Do not recommend a specific batch disposition such as release,
  rejection, or reprocessing.
- Do not make regulatory or final quality decisions.
- action_type must be either "Corrective" or "Preventive".
- status must always be "Proposed".
- Include an effectiveness check for every action.
- The effectiveness check should describe what should be verified,
  without inventing numerical targets or time periods.
- Leave owner and due_date empty unless explicitly provided.

Investigation text:
{state["source_text"]}

Identified evidence:
{state["evidence"]}

5 Whys analysis:
{state["five_whys"]}

Potential root causes:
{state["root_causes"]}

Missing evidence:
{state["missing_evidence"]}
"""

    response = llm.invoke(prompt)

    return {
        "capa": response.content
    }

# -----------------------------
# 4. LangGraph
# -----------------------------

graph_builder = StateGraph(RCAState)

graph_builder.add_node("extract_incident", extract_incident)
graph_builder.add_node("analyze_evidence", analyze_evidence)
graph_builder.add_node("five_whys", five_whys)
graph_builder.add_node("identify_root_causes", identify_root_causes)
graph_builder.add_node("identify_missing_evidence", identify_missing_evidence)
graph_builder.add_node("recommend_capa", recommend_capa)

graph_builder.add_edge(START, "extract_incident")
graph_builder.add_edge("extract_incident", "analyze_evidence")
graph_builder.add_edge("analyze_evidence", "five_whys")
graph_builder.add_edge("five_whys", "identify_root_causes")
graph_builder.add_edge("identify_root_causes", "identify_missing_evidence")
graph_builder.add_edge("identify_missing_evidence", "recommend_capa")
graph_builder.add_edge("recommend_capa", END)

rca_graph = graph_builder.compile()



