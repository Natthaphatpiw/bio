"""
Session Bundle - Aggregated signals for agent processing
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from .events import (
    EventType,
    IntegritySignal,
    LightSyncSignal,
    LivenessSignal,
    BehaviorSignal,
    TransactionContext,
)


class SessionBundle(BaseModel):
    """
    Aggregated session data for agent decision making.
    This is what gets passed to agent tools.
    """
    session_id: str
    event_type: EventType
    merchant_id: str = "default"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Core signals
    integrity: Optional[IntegritySignal] = None
    lightsync: Optional[LightSyncSignal] = None
    liveness: Optional[LivenessSignal] = None
    behavior_demo: Optional[BehaviorSignal] = None
    txn_context: Optional[TransactionContext] = None

    # Metadata
    device_fingerprint: Optional[str] = None
    app_version: Optional[str] = None

    # Computed risk scores (cached after tool calls)
    cached_scores: Dict[str, float] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for tool consumption"""
        return {
            "session_id": self.session_id,
            "event_type": self.event_type.value if self.event_type else None,
            "merchant_id": self.merchant_id,
            "integrity": self.integrity.model_dump() if self.integrity else {},
            "lightsync": self.lightsync.model_dump() if self.lightsync else {},
            "liveness": self.liveness.model_dump() if self.liveness else {},
            "behavior_demo": self.behavior_demo.model_dump() if self.behavior_demo else {},
            "txn_context": self.txn_context.model_dump() if self.txn_context else {},
        }

    @classmethod
    def from_event(cls, event: "SessionEvent", merchant_id: str = "default") -> "SessionBundle":
        """Create bundle from session event"""
        from .events import SessionEvent
        return cls(
            session_id=event.session_id,
            event_type=event.event_type,
            merchant_id=merchant_id,
            integrity=event.integrity,
            lightsync=event.lightsync,
            liveness=event.liveness,
            behavior_demo=event.behavior_demo,
            txn_context=event.txn_context,
            device_fingerprint=event.device_fingerprint,
            app_version=event.app_version,
        )


class StoredSignal(BaseModel):
    """Individual signal stored in feature store"""
    session_id: str
    signal_type: str  # integrity, lightsync, liveness, behavior, context
    raw_data: Dict[str, Any]
    processed_score: Optional[float] = None
    reason_codes: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StoredDecision(BaseModel):
    """Stored decision for audit trail"""
    session_id: str
    decision: str
    final_risk: float
    reason_codes: list[str]
    evidence: Dict[str, Any]
    next_action: Dict[str, Any]
    audit: Dict[str, Any]
    explanation: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
