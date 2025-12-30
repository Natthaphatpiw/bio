"""
Step-up Tools - Deterministic selection of verification challenges
"""
from typing import Dict, Any, List


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
    lightsync = ctx.get("lightsync", {}) or {}
    liveness = ctx.get("liveness", {}) or {}
    behavior = ctx.get("behavior", {}) or {}
    txn_context = ctx.get("txn_context", {}) or {}

    if action_type == "STEP_UP":
        if "LS_FAIL" in reason_codes or lightsync.get("is_injection_likely"):
            stepup_type = "retry_lightsync"
            user_message = "We need to verify your environment. Please retry the light sync check."
            ops_message = "Step-up via LightSync retry due to injection signals."
        elif "LIVENESS_FAIL" in reason_codes or liveness.get("is_spoof_likely"):
            stepup_type = "retry_liveness"
            user_message = "Please complete a quick liveness check to continue."
            ops_message = "Step-up via liveness retry due to spoof risk."
        elif "BEHAV_SESSION" in reason_codes or behavior.get("is_anomalous"):
            stepup_type = "biometric"
            user_message = "Please verify using biometric authentication."
            ops_message = "Step-up via biometric due to behavioral anomaly."
        elif txn_context.get("new_payee") or txn_context.get("amount_zscore", 0) > 2:
            stepup_type = "passkey"
            user_message = "Please confirm with a passkey to continue this transaction."
            ops_message = "Step-up via passkey due to high-risk transaction context."
        else:
            stepup_type = "otp_verify"
            user_message = "Please confirm your identity with a one-time passcode."
            ops_message = "Step-up via OTP to reduce risk."

        return {
            "type": stepup_type,
            "user_message": user_message,
            "ops_message": ops_message,
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
