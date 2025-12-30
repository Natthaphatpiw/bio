"""
Sessions Router - Agent-native verification endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime

from models.events import SessionEvent, EventType
from models.decisions import AgentDecision, DecisionType
from models.bundles import StoredDecision
from store.feature_store import get_feature_store
from agents.orchestrator import run_orchestrator
from tools.notification_tools import notify_dashboard, send_webhook
from config import get_merchant_config, get_settings

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SignalSubmitRequest(BaseModel):
    """Request to submit signals for a session"""
    event_type: str  # EKYC, LOGIN, ADD_PAYEE, TRANSFER
    merchant_id: str = "default"

    # Integrity signals
    integrity: Optional[Dict[str, Any]] = None

    # LightSync signals
    lightsync: Optional[Dict[str, Any]] = None

    # Liveness signals
    liveness: Optional[Dict[str, Any]] = None

    # Behavior signals (mock for demo)
    behavior: Optional[Dict[str, Any]] = None

    # Transaction context
    context: Optional[Dict[str, Any]] = None

    # Metadata
    device_id: Optional[str] = None
    user_id: Optional[str] = None


class SignalSubmitResponse(BaseModel):
    """Response from signal submission"""
    session_id: str
    decision: str
    final_risk: float
    reason_codes: List[str]
    explanation: str
    next_action: Dict[str, Any]
    case_id: Optional[str] = None


class SessionStatusResponse(BaseModel):
    """Response for session status"""
    session_id: str
    status: str
    has_decision: bool
    decision: Optional[str] = None
    final_risk: Optional[float] = None
    created_at: str


@router.post("/{session_id}/signals", response_model=SignalSubmitResponse)
async def submit_signals(
    session_id: str,
    request: SignalSubmitRequest,
    background_tasks: BackgroundTasks,
):
    """
    Submit all signals for a session and get agent decision.

    This is the main endpoint for mobile clients. It:
    1. Stores signals in feature store
    2. Runs the orchestrator agent
    3. Returns decision with explanation
    4. Triggers notifications in background
    """
    settings = get_settings()
    store = get_feature_store()

    # Build SessionEvent from request
    try:
        event_type = EventType(request.event_type.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event_type: {request.event_type}. Must be one of: EKYC, LOGIN, ADD_PAYEE, TRANSFER"
        )

    # Create session event with provided signals
    event = SessionEvent(
        session_id=session_id,
        event_type=event_type,
        timestamp=datetime.utcnow(),
        integrity=_build_integrity_signal(request.integrity),
        lightsync=_build_lightsync_signal(request.lightsync),
        liveness=_build_liveness_signal(request.liveness),
        behavior=_build_behavior_signal(request.behavior),
        context=_build_transaction_context(request.context, event_type),
        device_id=request.device_id,
        user_id=request.user_id,
    )

    # Store event in feature store
    await store.store_event(event)

    # Run orchestrator agent
    try:
        agent_decision: AgentDecision = await run_orchestrator(
            session_id=session_id,
            event_type=request.event_type,
            merchant_id=request.merchant_id,
            model=settings.openai_model,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent decision failed: {str(e)}"
        )

    # Store decision
    stored_decision = StoredDecision(
        session_id=session_id,
        decision=agent_decision.decision.value,
        final_risk=agent_decision.final_risk,
        reason_codes=agent_decision.reason_codes,
        explanation=agent_decision.explanation,
        evidence=_serialize_evidence(agent_decision.evidence),
        next_action=agent_decision.next_action.model_dump() if agent_decision.next_action else {},
        audit=agent_decision.audit.model_dump() if agent_decision.audit else {},
    )
    await store.store_decision(stored_decision)

    # Extract case_id if case was created
    case_id = None
    if agent_decision.audit and agent_decision.audit.tool_trace_refs:
        for trace in agent_decision.audit.tool_trace_refs:
            if trace.startswith("create_case:"):
                # Case was created during agent run
                case_id = trace.split(":")[1] if ":" in trace else None

    # Background notifications
    merchant_config = get_merchant_config(request.merchant_id)

    background_tasks.add_task(
        notify_dashboard,
        session_id=session_id,
        decision=agent_decision.decision.value,
        final_risk=agent_decision.final_risk,
        reason_codes=agent_decision.reason_codes,
        explanation=agent_decision.explanation,
        case_id=case_id,
    )

    if merchant_config.get("webhook_url"):
        background_tasks.add_task(
            send_webhook,
            webhook_url=merchant_config["webhook_url"],
            session_id=session_id,
            event_type="verification.completed",
            payload={
                "decision": agent_decision.decision.value,
                "final_risk": agent_decision.final_risk,
                "reason_codes": agent_decision.reason_codes,
            }
        )

    return SignalSubmitResponse(
        session_id=session_id,
        decision=agent_decision.decision.value,
        final_risk=agent_decision.final_risk,
        reason_codes=agent_decision.reason_codes,
        explanation=agent_decision.explanation,
        next_action=agent_decision.next_action.model_dump() if agent_decision.next_action else {},
        case_id=case_id,
    )


@router.get("/{session_id}/decision")
async def get_decision(session_id: str):
    """
    Get the latest decision for a session.
    """
    store = get_feature_store()
    decision = await store.get_decision(session_id)

    if not decision:
        raise HTTPException(
            status_code=404,
            detail=f"No decision found for session {session_id}"
        )

    return {
        "session_id": session_id,
        "decision": decision.decision,
        "final_risk": decision.final_risk,
        "reason_codes": decision.reason_codes,
        "explanation": decision.explanation,
        "next_action": decision.next_action,
        "created_at": decision.created_at.isoformat() if decision.created_at else None,
    }


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """
    Get the current status of a session.
    """
    store = get_feature_store()
    bundle = await store.get_bundle(session_id)
    decision = await store.get_decision(session_id)

    if not bundle:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )

    return SessionStatusResponse(
        session_id=session_id,
        status="completed" if decision else "pending",
        has_decision=decision is not None,
        decision=decision.decision if decision else None,
        final_risk=decision.final_risk if decision else None,
        created_at=bundle.timestamp.isoformat() if bundle.timestamp else datetime.utcnow().isoformat(),
    )


@router.get("/{session_id}/bundle")
async def get_session_bundle(session_id: str):
    """
    Get all signals for a session (for debugging/ops).
    """
    store = get_feature_store()
    bundle = await store.get_bundle(session_id)

    if not bundle:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )

    return bundle.to_dict()


# Helper functions to build signal objects from request data

def _build_integrity_signal(data: Optional[Dict]) -> Optional[Any]:
    """Build integrity signal from request data"""
    if not data:
        return None

    from models.events import IntegritySignal
    return IntegritySignal(
        is_emulator=data.get("is_emulator", False),
        is_rooted=data.get("is_rooted", False),
        is_hooking=data.get("is_hooking", False),
        is_debuggable=data.get("is_debuggable", False),
        is_vpn=data.get("is_vpn", False),
        is_proxy=data.get("is_proxy", False),
        app_signature_valid=data.get("app_signature_valid", True),
        device_binding_valid=data.get("device_binding_valid", True),
        raw_data=data.get("raw_data", {}),
    )


def _build_lightsync_signal(data: Optional[Dict]) -> Optional[Any]:
    """Build lightsync signal from request data"""
    if not data:
        return None

    from models.events import LightSyncSignal
    return LightSyncSignal(
        score=data.get("score", 0.0),
        quality=data.get("quality", "unknown"),
        rounds_passed=data.get("rounds_passed", 0),
        rounds_total=data.get("rounds_total", 3),
        raw_data=data.get("raw_data", {}),
    )


def _build_liveness_signal(data: Optional[Dict]) -> Optional[Any]:
    """Build liveness signal from request data"""
    if not data:
        return None

    from models.events import LivenessSignal
    return LivenessSignal(
        score=data.get("score", 0.0),
        quality=data.get("quality", "unknown"),
        is_real=data.get("is_real", False),
        confidence=data.get("confidence", 0.0),
        raw_data=data.get("raw_data", {}),
    )


def _build_behavior_signal(data: Optional[Dict]) -> Optional[Any]:
    """Build behavior signal from request data (mock)"""
    if not data:
        return None

    from models.events import BehaviorSignal
    return BehaviorSignal(
        anomaly_score=data.get("anomaly_score", 0.0),
        velocity_risk=data.get("velocity_risk", 0.0),
        session_duration_seconds=data.get("session_duration_seconds", 0),
        interaction_patterns=data.get("interaction_patterns", {}),
        risk_indicators=data.get("risk_indicators", []),
        raw_data=data.get("raw_data", {}),
    )


def _build_transaction_context(data: Optional[Dict], event_type: EventType) -> Optional[Any]:
    """Build transaction context from request data"""
    if not data and event_type not in [EventType.ADD_PAYEE, EventType.TRANSFER]:
        return None

    from models.events import TransactionContext

    if not data:
        data = {}

    return TransactionContext(
        amount=data.get("amount"),
        currency=data.get("currency", "THB"),
        recipient_id=data.get("recipient_id"),
        recipient_name=data.get("recipient_name"),
        is_new_payee=data.get("is_new_payee", False),
        device_age_days=data.get("device_age_days", 0),
        user_account_age_days=data.get("user_account_age_days", 0),
        transaction_count_24h=data.get("transaction_count_24h", 0),
    )


def _serialize_evidence(evidence) -> Dict[str, Any]:
    """Serialize evidence object to dict"""
    if not evidence:
        return {}

    return {
        "integrity": evidence.integrity.model_dump() if evidence.integrity else {},
        "lightsync": evidence.lightsync.model_dump() if evidence.lightsync else {},
        "liveness": evidence.liveness.model_dump() if evidence.liveness else {},
        "behavior": evidence.behavior.model_dump() if evidence.behavior else {},
        "policy": evidence.policy.model_dump() if evidence.policy else {},
    }
