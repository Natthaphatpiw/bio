"""
Decision schemas - Output from Agent Orchestrator
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DecisionType(str, Enum):
    """Agent decision types"""
    ALLOW = "ALLOW"      # User passes, proceed with transaction
    STEP_UP = "STEP_UP"  # Suspicious, require additional verification
    HOLD = "HOLD"        # High risk, freeze pending manual review
    BLOCK = "BLOCK"      # Clear fraud, reject immediately


class StepUpType(str, Enum):
    """Types of step-up verification"""
    NONE = "none"
    RETRY_LIGHTSYNC = "retry_lightsync"
    RETRY_LIVENESS = "retry_liveness"
    OTP_VERIFY = "otp_verify"
    BIOMETRIC = "biometric"
    PASSKEY = "passkey"
    BEHAVIOR_PHRASE = "behavior_phrase"
    MANUAL_REVIEW = "manual_review"
    VIDEO_CALL = "video_call"


class NextAction(BaseModel):
    """What should happen after decision"""
    type: StepUpType = StepUpType.NONE
    user_message: str = Field(
        description="Human-readable message for end user (helpful, not accusatory)"
    )
    ops_message: str = Field(
        description="Message for ops/fraud team"
    )
    challenge: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional challenge payload (e.g., behavioral phrase prompt)"
    )
    timeout_seconds: int = Field(default=300, ge=0)
    retry_allowed: bool = True
    max_retries: int = 3


class SignalEvidence(BaseModel):
    """Evidence from a single signal domain"""
    score: float = Field(ge=0, le=1)
    reason_codes: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class PolicyEvidence(BaseModel):
    """Evidence from policy engine"""
    min_action: str  # ALLOW, STEP_UP, HOLD, BLOCK
    triggered_rules: List[str] = Field(default_factory=list)
    can_allow: bool = True
    must_block: bool = False


class Evidence(BaseModel):
    """Complete evidence breakdown"""
    integrity: SignalEvidence
    lightsync: SignalEvidence
    liveness: SignalEvidence
    behavior: SignalEvidence
    policy: PolicyEvidence
    context: Optional[Dict[str, Any]] = None


class AuditInfo(BaseModel):
    """Audit trail for compliance and debugging"""
    session_id: str
    agent_run_id: str = Field(default="")
    tool_trace_refs: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = "gpt-5-mini"
    latency_ms: float = 0.0
    token_usage: Optional[Dict[str, int]] = None


class AgentDecision(BaseModel):
    """
    Complete decision output from Agent Orchestrator
    This is the main output sent to mobile app and dashboard
    """
    decision: DecisionType
    final_risk: float = Field(ge=0, le=1)
    reason_codes: List[str] = Field(
        description="Specific codes for transparency and analytics"
    )
    evidence: Evidence
    next_action: NextAction
    audit: AuditInfo
    explanation: str = Field(
        description="Human-readable explanation of the decision"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "decision": "ALLOW",
                "final_risk": 0.15,
                "reason_codes": ["ENV_DEV_MODE"],
                "evidence": {
                    "integrity": {"score": 0.3, "reason_codes": ["ENV_DEV_MODE"]},
                    "lightsync": {"score": 0.1, "reason_codes": []},
                    "liveness": {"score": 0.1, "reason_codes": []},
                    "behavior": {"score": 0.1, "reason_codes": []},
                    "policy": {"min_action": "ALLOW", "triggered_rules": []}
                },
                "next_action": {
                    "type": "none",
                    "user_message": "Verification complete",
                    "ops_message": "Clean session"
                },
                "audit": {
                    "session_id": "sess_abc123",
                    "agent_run_id": "run_xyz",
                    "tool_trace_refs": []
                },
                "explanation": "All signals within acceptable thresholds. Low-value transfer from established device."
            }
        }


class DecisionResponse(BaseModel):
    """API response for decision endpoint"""
    session_id: str
    decision: DecisionType
    final_risk: float
    reason_codes: List[str]
    next_action: Dict[str, Any]
    explanation: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
