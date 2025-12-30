"""
Adaptive Verification Orchestrator Agent

Main agent that makes ALLOW/STEP_UP/HOLD/BLOCK decisions
using OpenAI Agents SDK.
"""
import time
import uuid
from dataclasses import dataclass
from contextvars import ContextVar
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from agents import (
    Agent,
    Runner,
    SQLiteSession,
    InputGuardrail,
    GuardrailFunctionOutput,
    ModelSettings,
    function_tool,
)
from agents.exceptions import InputGuardrailTripwireTriggered

from config import get_settings
from models.decisions import (
    AgentDecision,
    DecisionType,
    StepUpType,
    NextAction,
    AuditInfo,
    Evidence,
    SignalEvidence,
    PolicyEvidence,
)
from tools import session_tools, scoring_tools, policy_tools, case_tools, stepup_tools
from agents.prompts.orchestrator_system import ORCHESTRATOR_SYSTEM_PROMPT


@dataclass
class OrchestratorContext:
    """Context passed to orchestrator"""
    session_id: str
    event_type: str
    merchant_id: str = "default"


class InputCheck(BaseModel):
    ok: bool
    reason: str


class DecisionDraft(BaseModel):
    decision: DecisionType
    final_risk: float = Field(ge=0.0, le=1.0)
    reason_codes: List[str] = Field(default_factory=list)
    evidence: Evidence
    next_action: NextAction
    explanation: str


_tool_trace_var: ContextVar[Optional[List[str]]] = ContextVar("tool_trace_refs", default=None)


def _record_tool_call(name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    trace = _tool_trace_var.get()
    if trace is not None:
        trace.append(name)
    return result


@function_tool
def get_session_bundle(session_id: str) -> Dict[str, Any]:
    """Fetch latest signals/features for a session from feature store."""
    result = session_tools.get_session_bundle(session_id)
    return _record_tool_call("get_session_bundle", result)


@function_tool
def score_integrity(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Return integrity risk + evidence."""
    result = scoring_tools.score_integrity(bundle)
    return _record_tool_call("score_integrity", result)


@function_tool
def score_lightsync(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Return injection risk based on lightsync."""
    result = scoring_tools.score_lightsync(bundle)
    return _record_tool_call("score_lightsync", result)


@function_tool
def score_liveness(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Return liveness risk."""
    result = scoring_tools.score_liveness(bundle)
    return _record_tool_call("score_liveness", result)


@function_tool
def score_behavior(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Return behavior risk (demo)."""
    result = scoring_tools.score_behavior(bundle)
    return _record_tool_call("score_behavior", result)


@function_tool
def score_context(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Return transaction context risk."""
    result = scoring_tools.score_context(bundle)
    return _record_tool_call("score_context", result)


@function_tool
def policy_floor(bundle: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, Any]:
    """Return hard constraints: min_action, risk_floor, rule_hits."""
    result = policy_tools.policy_floor(bundle, scores)
    return _record_tool_call("policy_floor", result)


@function_tool
def decide_stepup(action_type: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Return step-up plan based on action type and context."""
    result = stepup_tools.decide_stepup(action_type, ctx)
    return _record_tool_call("decide_stepup", result)


@function_tool
def create_case(
    session_id: str,
    summary: str,
    severity: str,
    evidence_refs: List[str],
) -> Dict[str, Any]:
    """Create an ops case."""
    result = case_tools.create_case(session_id, summary, severity, evidence_refs)
    case_id = result.get("case_id")
    trace_name = f"create_case:{case_id}" if case_id else "create_case"
    return _record_tool_call(trace_name, result)


guardrail_agent = Agent(
    name="Input Guardrail",
    instructions=(
        "Validate that the input does not contain raw biometrics/images/keystrokes "
        "and is a request to run a verification decision. Return ok=true/false."
    ),
    output_type=InputCheck,
    model="gpt-5-mini",
)


async def input_guardrail(ctx, agent, input_data):
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
    out = result.final_output_as(InputCheck)
    return GuardrailFunctionOutput(output_info=out, tripwire_triggered=not out.ok)


_DECISION_RANK = {
    DecisionType.ALLOW: 0,
    DecisionType.STEP_UP: 1,
    DecisionType.HOLD: 2,
    DecisionType.BLOCK: 3,
}


def _collect_reason_codes(evidence: Evidence) -> List[str]:
    codes: List[str] = []
    for segment in [
        evidence.integrity,
        evidence.lightsync,
        evidence.liveness,
        evidence.behavior,
    ]:
        if segment and segment.reason_codes:
            codes.extend(segment.reason_codes)
    context = evidence.context or {}
    context_codes = context.get("reason_codes", []) if isinstance(context, dict) else []
    if context_codes:
        codes.extend(context_codes)
    policy_codes = evidence.policy.triggered_rules if evidence.policy else []
    if policy_codes:
        codes.extend(policy_codes)
    return codes


def _dedupe_codes(codes: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for code in codes:
        if code and code not in seen:
            seen.add(code)
            result.append(code)
    return result


def _next_action_from_payload(payload: Dict[str, Any]) -> NextAction:
    try:
        stepup_type = StepUpType(payload.get("type", "none"))
    except ValueError:
        stepup_type = StepUpType.NONE

    return NextAction(
        type=stepup_type,
        user_message=payload.get("user_message", "Verification complete."),
        ops_message=payload.get("ops_message", "Session processed."),
        timeout_seconds=int(payload.get("timeout_seconds", 300)),
        retry_allowed=bool(payload.get("retry_allowed", True)),
        max_retries=int(payload.get("max_retries", 3)),
    )


def _empty_evidence(min_action: str = "BLOCK") -> Evidence:
    empty_signal = SignalEvidence(score=0.0, reason_codes=[], details={})
    policy = PolicyEvidence(
        min_action=min_action,
        triggered_rules=[],
        can_allow=False,
        must_block=min_action == "BLOCK",
    )
    return Evidence(
        integrity=empty_signal,
        lightsync=empty_signal,
        liveness=empty_signal,
        behavior=empty_signal,
        policy=policy,
    )


def _build_stepup_context(
    bundle: Dict[str, Any],
    scores: Dict[str, Any],
    reason_codes: List[str],
) -> Dict[str, Any]:
    return {
        "event_type": bundle.get("event_type"),
        "reason_codes": reason_codes,
        "integrity": scores.get("integrity", {}),
        "lightsync": scores.get("lightsync", {}),
        "liveness": scores.get("liveness", {}),
        "behavior": scores.get("behavior", {}),
        "txn_context": bundle.get("txn_context", {}),
    }


def _enforce_policy_floor(session_id: str, draft: DecisionDraft) -> DecisionDraft:
    bundle = session_tools.get_session_bundle(session_id)
    if not bundle or "error" in bundle:
        return draft

    scores = {
        "integrity": scoring_tools.score_integrity(bundle),
        "lightsync": scoring_tools.score_lightsync(bundle),
        "liveness": scoring_tools.score_liveness(bundle),
        "behavior": scoring_tools.score_behavior(bundle),
        "context": scoring_tools.score_context(bundle),
    }
    policy = policy_tools.policy_floor(bundle, scores)

    if not draft.evidence.context:
        draft.evidence.context = scores.get("context", {})

    # Update policy evidence based on deterministic policy engine
    draft.evidence.policy = PolicyEvidence(
        min_action=policy.get("min_action", "ALLOW"),
        triggered_rules=policy.get("triggered_rules", []),
        can_allow=policy.get("can_allow", True),
        must_block=policy.get("must_block", False),
    )

    try:
        min_action = DecisionType(policy.get("min_action", "ALLOW"))
    except ValueError:
        min_action = DecisionType.ALLOW
    if _DECISION_RANK[draft.decision] < _DECISION_RANK[min_action]:
        draft.decision = min_action
        draft.reason_codes = _dedupe_codes(draft.reason_codes + ["POLICY_FLOOR"])

        if min_action != DecisionType.ALLOW:
            stepup_payload = stepup_tools.decide_stepup(
                min_action.value,
                _build_stepup_context(bundle, scores, draft.reason_codes),
            )
            draft.next_action = _next_action_from_payload(stepup_payload)

    risk_floor = float(policy.get("risk_floor", 0.0))
    draft.final_risk = min(max(max(draft.final_risk, risk_floor), 0.0), 1.0)

    # Ensure reason_codes at least reflect evidence
    if not draft.reason_codes:
        draft.reason_codes = _collect_reason_codes(draft.evidence)
    draft.reason_codes = _dedupe_codes(draft.reason_codes)

    return draft


def build_orchestrator_agent(model: str, temperature: float) -> Agent:
    return Agent(
        name="BioGuard Orchestrator",
        instructions=ORCHESTRATOR_SYSTEM_PROMPT,
        model=model,
        model_settings=ModelSettings(temperature=temperature),
        tools=[
            get_session_bundle,
            score_integrity,
            score_lightsync,
            score_liveness,
            score_behavior,
            score_context,
            policy_floor,
            decide_stepup,
            create_case,
        ],
        output_type=DecisionDraft,
        input_guardrails=[InputGuardrail(guardrail_function=input_guardrail)],
    )


async def run_orchestrator(
    session_id: str,
    event_type: str,
    merchant_id: str = "default",
    model: Optional[str] = None,
) -> AgentDecision:
    """
    Run the orchestrator agent for a verification decision.
    """
    settings = get_settings()
    model_name = model or settings.openai_model

    start_time = time.time()
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    tool_traces: List[str] = []
    trace_token = _tool_trace_var.set([])

    try:
        session = SQLiteSession(session_id)
        agent = build_orchestrator_agent(model_name, settings.agent_temperature)

        user_message = (
            "Evaluate verification session and make a decision.\n\n"
            f"Session ID: {session_id}\n"
            f"Event Type: {event_type}\n"
            f"Merchant ID: {merchant_id}\n\n"
            "Follow these steps:\n"
            "1. Fetch the session bundle using get_session_bundle\n"
            "2. Score each signal domain (integrity, lightsync, liveness, behavior, context)\n"
            "3. Check policy_floor for hard constraints\n"
            "4. Make adaptive decision considering all factors\n"
            "5. Choose step-up action if needed (decide_stepup)\n"
            "6. If HOLD or BLOCK, create a case automatically\n"
            "7. Return your decision as a JSON object following the schema in your instructions\n"
        )

        result = await Runner.run(
            agent,
            user_message,
            context=OrchestratorContext(
                session_id=session_id,
                event_type=event_type,
                merchant_id=merchant_id,
            ),
            session=session,
            max_turns=settings.agent_max_iterations,
        )

        draft = result.final_output_as(DecisionDraft)
        draft = _enforce_policy_floor(session_id, draft)
    except InputGuardrailTripwireTriggered as e:
        audit = AuditInfo(
            session_id=session_id,
            agent_run_id=run_id,
            tool_trace_refs=[],
            model_used=model_name,
            latency_ms=(time.time() - start_time) * 1000,
        )
        return AgentDecision(
            decision=DecisionType.BLOCK,
            final_risk=1.0,
            reason_codes=["INPUT_GUARDRAIL"],
            evidence=_empty_evidence(min_action="BLOCK"),
            next_action=NextAction(
                type=StepUpType.MANUAL_REVIEW,
                user_message="We couldn't complete verification. Please contact support.",
                ops_message="Blocked by input guardrail.",
                timeout_seconds=0,
                retry_allowed=False,
                max_retries=0,
            ),
            audit=audit,
            explanation=f"Blocked by input guardrail: {e}",
        )
    finally:
        tool_traces = _tool_trace_var.get() or []
        _tool_trace_var.reset(trace_token)

    latency_ms = (time.time() - start_time) * 1000

    audit = AuditInfo(
        session_id=session_id,
        agent_run_id=run_id,
        tool_trace_refs=tool_traces,
        model_used=model_name,
        latency_ms=latency_ms,
    )

    return AgentDecision(
        decision=draft.decision,
        final_risk=draft.final_risk,
        reason_codes=draft.reason_codes,
        evidence=draft.evidence,
        next_action=draft.next_action,
        audit=audit,
        explanation=draft.explanation,
    )


def run_orchestrator_sync(
    session_id: str,
    event_type: str,
    merchant_id: str = "default",
    model: Optional[str] = None,
) -> AgentDecision:
    """
    Synchronous wrapper for run_orchestrator.
    """
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    run_orchestrator(session_id, event_type, merchant_id, model),
                )
                return future.result()
        else:
            return asyncio.run(
                run_orchestrator(session_id, event_type, merchant_id, model)
            )
    except RuntimeError:
        return asyncio.run(
            run_orchestrator(session_id, event_type, merchant_id, model)
        )


# Export the agent for external use
orchestrator_agent = build_orchestrator_agent(
    get_settings().openai_model,
    get_settings().agent_temperature,
)
