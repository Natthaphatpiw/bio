"""
Event schemas - Input from mobile app (Canonical Event Schema)
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Type of verification event"""
    EKYC = "EKYC"
    LOGIN = "LOGIN"
    ADD_PAYEE = "ADD_PAYEE"
    TRANSFER = "TRANSFER"


class IntegritySignal(BaseModel):
    """Module A: Environment Shield signals"""
    is_emulator: bool = False
    is_rooted: bool = False
    is_dev_mode: bool = False
    is_usb_debug: bool = False
    is_hooking: bool = False
    confidence: float = Field(default=1.0, ge=0, le=1)
    raw_checks: Optional[Dict[str, Any]] = None

    @property
    def is_compromised(self) -> bool:
        """Check if any critical flag is set"""
        return self.is_emulator or self.is_rooted or self.is_hooking


class LightSyncSignal(BaseModel):
    """Module B: Light-Sync Challenge signals"""
    score: float = Field(ge=0, le=1, description="Confidence score (higher = more confident real)")
    quality: float = Field(ge=0, le=1, description="Capture quality")
    rounds_passed: int = Field(ge=0, default=0)
    rounds_total: int = Field(ge=1, default=3)
    analysis: Optional[Dict[str, Any]] = None

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate"""
        return self.rounds_passed / max(self.rounds_total, 1)

    @property
    def is_suspicious(self) -> bool:
        """Check if light-sync indicates injection"""
        return self.pass_rate < 0.5 or self.quality < 0.4


class LivenessSignal(BaseModel):
    """Module C: Face Liveness signals"""
    score: float = Field(ge=0, le=1, description="Real probability")
    quality: float = Field(ge=0, le=1, default=0.7)
    is_real: bool = False
    probabilities: Optional[Dict[str, float]] = None
    model_version: str = "MiniFASNetV1SE"

    @property
    def is_suspicious(self) -> bool:
        """Check if liveness indicates spoofing"""
        return not self.is_real or self.score < 0.7


class BehaviorSignal(BaseModel):
    """
    Behavioral Biometrics signals (Mock for demo)
    In production: typing patterns, swipe dynamics, motion analysis
    """
    session_embedding: Optional[List[float]] = None
    feature_stats: Optional[Dict[str, float]] = None
    anomaly_score: float = Field(default=0.1, ge=0, le=1)
    risk_indicators: List[str] = Field(default_factory=list)
    is_mock: bool = True

    @property
    def is_anomalous(self) -> bool:
        """Check if behavior is anomalous"""
        return self.anomaly_score > 0.5 or len(self.risk_indicators) > 0


class TransactionContext(BaseModel):
    """Transaction context for risk assessment"""
    new_payee: bool = False
    amount: float = 0.0
    amount_zscore: float = 0.0  # Standard deviations from user's average
    recipient_risk_score: float = 0.0
    device_age_days: int = 0
    last_login_hours_ago: float = 0.0
    ip_risk: float = 0.0
    time_of_day_risk: float = 0.0

    @property
    def is_high_risk(self) -> bool:
        """Check if transaction context is high risk"""
        return (
            (self.new_payee and self.amount > 5000) or
            self.amount_zscore > 2.0 or
            self.recipient_risk_score > 0.5
        )


class SessionEvent(BaseModel):
    """
    Canonical event schema from mobile app
    This is the main input to the Agent Orchestrator
    """
    session_id: str
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Core signals from verification modules
    integrity: IntegritySignal
    lightsync: LightSyncSignal
    liveness: LivenessSignal

    # Optional signals
    behavior_demo: Optional[BehaviorSignal] = None
    txn_context: Optional[TransactionContext] = None

    # Metadata
    device_fingerprint: Optional[str] = None
    app_version: Optional[str] = None
    nonce: Optional[str] = None
    signature: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "event_type": "TRANSFER",
                "integrity": {
                    "is_emulator": False,
                    "is_rooted": False,
                    "is_hooking": False
                },
                "lightsync": {
                    "score": 0.85,
                    "quality": 0.76,
                    "rounds_passed": 3,
                    "rounds_total": 3
                },
                "liveness": {
                    "score": 0.92,
                    "quality": 0.8,
                    "is_real": True
                },
                "behavior_demo": {
                    "anomaly_score": 0.1,
                    "risk_indicators": []
                },
                "txn_context": {
                    "new_payee": False,
                    "amount": 1000
                }
            }
        }
