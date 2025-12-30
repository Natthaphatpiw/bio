"""
Fraud Case Copilot Agent

AI assistant for fraud operations team to investigate cases.
Uses OpenAI Agents SDK with tools and structured output.
"""
import time
from dataclasses import dataclass
from contextvars import ContextVar
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field

from agents import Agent, Runner, SQLiteSession, ModelSettings, function_tool

from config import get_settings
from tools.case_tools import (
    get_case,
    list_cases,
    add_case_comment,
    summarize_case_timeline,
)
from store.feature_store import get_feature_store
from agents.prompts.copilot_system import COPILOT_SYSTEM_PROMPT


@dataclass
class CopilotContext:
    case_id: str


class CopilotOutput(BaseModel):
    response: str
    suggested_actions: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[str] = Field(default_factory=list)


_tool_trace_var: ContextVar[Optional[List[str]]] = ContextVar("copilot_tool_trace_refs", default=None)


def _record_tool_call(name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    trace = _tool_trace_var.get()
    if trace is not None:
        trace.append(name)
    return result


@function_tool
def get_case_details(case_id: str) -> Dict[str, Any]:
    """Get detailed case information"""
    case = get_case(case_id)
    result = case if case else {"error": f"Case {case_id} not found"}
    return _record_tool_call("get_case_details", result)


@function_tool
def get_session_signals(session_id: str) -> Dict[str, Any]:
    """Get session signals from feature store"""
    import asyncio

    async def _fetch():
        store = get_feature_store()
        bundle = await store.get_bundle(session_id)
        if bundle:
            return bundle.to_dict()
        return {"error": f"Session {session_id} not found"}

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _fetch())
                result = future.result()
        else:
            result = asyncio.run(_fetch())
    except RuntimeError:
        result = asyncio.run(_fetch())

    return _record_tool_call("get_session_signals", result)


@function_tool
def find_similar_cases(case_id: str, limit: int = 5) -> Dict[str, Any]:
    """Find similar cases based on evidence patterns"""
    case = get_case(case_id)
    if not case:
        return _record_tool_call("find_similar_cases", {"error": f"Case {case_id} not found"})

    all_cases = list_cases(limit=100)
    similar = []

    for other_case in all_cases:
        if other_case["id"] == case_id:
            continue

        similarity_score = 0.0

        if other_case["severity"] == case["severity"]:
            similarity_score += 0.3

        case_evidence = set(case.get("evidence_refs", []))
        other_evidence = set(other_case.get("evidence_refs", []))
        if case_evidence and other_evidence:
            overlap = len(case_evidence & other_evidence) / max(len(case_evidence | other_evidence), 1)
            similarity_score += overlap * 0.5

        if other_case["status"] in ["CONFIRMED_FRAUD", "FALSE_POSITIVE"]:
            similarity_score += 0.2

        if similarity_score > 0.2:
            similar.append({
                "case_id": other_case["id"],
                "similarity_score": round(similarity_score, 2),
                "severity": other_case["severity"],
                "status": other_case["status"],
                "summary": other_case.get("summary", "")[:100],
                "resolution": other_case.get("resolution"),
            })

    similar.sort(key=lambda x: x["similarity_score"], reverse=True)

    result = {
        "case_id": case_id,
        "similar_cases": similar[:limit],
        "total_found": len(similar),
    }
    return _record_tool_call("find_similar_cases", result)


@function_tool
def get_case_timeline(case_id: str) -> Dict[str, Any]:
    """Get case timeline"""
    result = summarize_case_timeline(case_id)
    return _record_tool_call("get_case_timeline", result)


@function_tool
def add_investigation_note(case_id: str, note: str) -> Dict[str, Any]:
    """Add AI-generated note to case"""
    result = add_case_comment(
        case_id=case_id,
        author="AI Copilot",
        content=note,
        is_ai_generated=True,
    )
    return _record_tool_call("add_investigation_note", result)


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _extract_suggested_actions(content: str) -> List[str]:
    """Extract suggested actions from copilot response"""
    actions = []
    action_keywords = [
        "recommend",
        "suggest",
        "should",
        "action",
        "next step",
        "investigate",
        "verify",
        "contact",
        "block",
        "escalate",
    ]

    lines = content.split("\n")
    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in action_keywords):
            clean_line = line.strip()
            if clean_line.startswith(("-", "*", "•", "1.", "2.", "3.")):
                clean_line = clean_line.lstrip("-*•0123456789. ")
            if clean_line and len(clean_line) > 10:
                actions.append(clean_line[:200])

    return _dedupe(actions)[:5]


def build_fraud_copilot_agent(model: str, temperature: float) -> Agent:
    return Agent(
        name="Fraud Case Copilot",
        instructions=COPILOT_SYSTEM_PROMPT,
        model=model,
        model_settings=ModelSettings(temperature=temperature),
        tools=[
            get_case_details,
            get_session_signals,
            find_similar_cases,
            get_case_timeline,
            add_investigation_note,
        ],
        output_type=CopilotOutput,
    )


async def run_fraud_copilot(
    case_id: str,
    case_data: Dict[str, Any],
    user_message: str,
    context: Optional[Dict[str, Any]] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the fraud copilot agent for a case investigation.
    """
    settings = get_settings()
    model_name = model or settings.openai_model

    start_time = time.time()
    trace_token = _tool_trace_var.set([])

    context_str = (
        "Current Case Context:\n"
        f"- Case ID: {case_id}\n"
        f"- Status: {case_data.get('status', 'UNKNOWN')}\n"
        f"- Severity: {case_data.get('severity', 'UNKNOWN')}\n"
        f"- Session ID: {case_data.get('session_id', 'UNKNOWN')}\n"
        f"- Summary: {case_data.get('summary', 'No summary available')}\n"
        f"- Evidence Refs: {case_data.get('evidence_refs', [])}\n"
        f"- Created: {case_data.get('created_at', 'Unknown')}\n"
    )

    if context:
        context_str += f"\nAdditional Context: {context}"

    try:
        agent = build_fraud_copilot_agent(model_name, settings.agent_temperature)
        session = SQLiteSession(case_id)

        result = await Runner.run(
            agent,
            f"{context_str}\n\nUser Question: {user_message}",
            context=CopilotContext(case_id=case_id),
            session=session,
            max_turns=min(settings.agent_max_iterations, 6),
        )

        draft = result.final_output_as(CopilotOutput)
    finally:
        tool_traces = _tool_trace_var.get() or []
        _tool_trace_var.reset(trace_token)

    suggested_actions = draft.suggested_actions or _extract_suggested_actions(draft.response)
    sources = _dedupe(draft.sources + [f"case:{case_id}"] + [f"tool:{t}" for t in tool_traces])
    confidence = min(max(float(draft.confidence), 0.0), 1.0)

    latency_ms = (time.time() - start_time) * 1000

    return {
        "response": draft.response,
        "suggested_actions": suggested_actions,
        "confidence": confidence,
        "sources": sources,
        "latency_ms": latency_ms,
    }


# Export for external use
fraud_copilot_agent = build_fraud_copilot_agent(
    get_settings().openai_model,
    get_settings().agent_temperature,
)
