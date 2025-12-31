"""
Step-up Tools - Deterministic selection of verification challenges
"""
import hashlib
from typing import Dict, Any, List

_PHRASE_POOL = [
    "secure access",
    "verify device",
    "confirm transfer",
    "account secure",
    "trusted session",
    "safe login",
]


def _select_phrase(seed: str) -> Dict[str, Any]:
    if not seed:
        seed = "default"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(_PHRASE_POOL)
    text = _PHRASE_POOL[idx]
    return {
        "prompt_id": f"phrase_{idx}",
        "prompt_text": text,
        "min_chars": max(len(text), 8),
        "max_chars": max(len(text) + 6, 16),
    }


def decide_stepup(action_type: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decide the best step-up action based on context and evidence.

    Args:
        action_type: STEP_UP, HOLD, or BLOCK
        ctx: Context bundle including event_type, reason_codes, signals, and txn_context

    Returns:
        Dict with next_action fields (type, user_message, ops_message, etc.)
    """
    action_type = (action_type or "").upper()
    reason_codes: List[str] = ctx.get("reason_codes", []) or []

    event_type = ctx.get("event_type", "")
    session_id = ctx.get("session_id", "")
    lightsync = ctx.get("lightsync", {}) or {}
    liveness = ctx.get("liveness", {}) or {}
    behavior = ctx.get("behavior", {}) or {}
    txn_context = ctx.get("txn_context", {}) or {}
    preference = ctx.get("stepup_preference")

    if action_type == "STEP_UP":
        behavior_score = float(behavior.get("score", 0.0))
        behavior_anomaly = behavior.get("is_anomalous") or behavior_score >= 0.6
        context_risky = bool(
            txn_context.get("new_payee")
            or txn_context.get("amount_zscore", 0) > 2
            or txn_context.get("ip_risk", 0) > 0.5
        )

        if preference == "behavior_phrase":
            stepup_type = "behavior_phrase"
            challenge = _select_phrase(session_id or event_type)
            user_message = "Please type the verification phrase to continue."
            ops_message = "Step-up via behavioral phrase due to agent preference."
        elif "LS_FAIL" in reason_codes or lightsync.get("is_injection_likely"):
            stepup_type = "retry_lightsync"
            user_message = "We need to verify your environment. Please retry the light sync check."
            ops_message = "Step-up via LightSync retry due to injection signals."
            challenge = None
        elif "LIVENESS_FAIL" in reason_codes or liveness.get("is_spoof_likely"):
            stepup_type = "retry_liveness"
            user_message = "Please complete a quick liveness check to continue."
            ops_message = "Step-up via liveness retry due to spoof risk."
            challenge = None
        elif behavior_anomaly and context_risky:
            stepup_type = "behavior_phrase"
            challenge = _select_phrase(session_id or event_type)
            user_message = "Please type the verification phrase to continue."
            ops_message = "Step-up via behavioral phrase due to behavior anomaly."
        elif "BEHAV_SESSION" in reason_codes or behavior.get("is_anomalous"):
            stepup_type = "biometric"
            user_message = "Please verify using biometric authentication."
            ops_message = "Step-up via biometric due to behavioral anomaly."
            challenge = None
        elif txn_context.get("new_payee") or txn_context.get("amount_zscore", 0) > 2:
            stepup_type = "passkey"
            user_message = "Please confirm with a passkey to continue this transaction."
            ops_message = "Step-up via passkey due to high-risk transaction context."
            challenge = None
        else:
            stepup_type = "otp_verify"
            user_message = "Please confirm your identity with a one-time passcode."
            ops_message = "Step-up via OTP to reduce risk."
            challenge = None

        return {
            "type": stepup_type,
            "user_message": user_message,
            "ops_message": ops_message,
            "challenge": challenge,
            "timeout_seconds": 300,
            "retry_allowed": True,
            "max_retries": 2,
        }

    if action_type == "HOLD":
        return {
            "type": "manual_review",
            "user_message": "Your request is under security review. We'll update you shortly.",
            "ops_message": "Hold for manual review due to elevated risk signals.",
            "timeout_seconds": 900,
            "retry_allowed": False,
            "max_retries": 0,
        }

    if action_type == "BLOCK":
        return {
            "type": "manual_review",
            "user_message": "We couldn't complete verification. Please contact support.",
            "ops_message": "Block due to critical risk signals. Recommend account checks.",
            "timeout_seconds": 0,
            "retry_allowed": False,
            "max_retries": 0,
        }

    return {
        "type": "none",
        "user_message": "Verification complete.",
        "ops_message": "No additional action required.",
        "timeout_seconds": 0,
        "retry_allowed": False,
        "max_retries": 0,
    }
