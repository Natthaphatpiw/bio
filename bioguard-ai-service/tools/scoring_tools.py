"""
Scoring Tools - Calculate risk scores for each signal domain
"""
from typing import Dict, Any, List


def score_integrity(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate environment/integrity risk score.
    Checks for root, emulator, hooking, dev mode, USB debug.

    Args:
        bundle: Session bundle containing integrity signals

    Returns:
        Score (0-1 where 1=highest risk), reason_codes list, and risk breakdown
    """
    integrity = bundle.get("integrity", {})

    risk_score = 0.0
    reason_codes: List[str] = []
    breakdown = {}

    # Critical flags (immediate high risk)
    if integrity.get("is_hooking"):
        risk_score = 0.99
        reason_codes.append("ENV_HOOKING")
        breakdown["hooking"] = "DETECTED - Frida/Xposed injection suspected"

    if integrity.get("is_rooted"):
        risk_score = max(risk_score, 0.85)
        reason_codes.append("ENV_ROOTED")
        breakdown["root"] = "DETECTED - Device has superuser access"

    if integrity.get("is_emulator"):
        risk_score = max(risk_score, 0.9)
        reason_codes.append("ENV_EMULATOR")
        breakdown["emulator"] = "DETECTED - Running in virtual environment"

    # Warning flags (elevated risk)
    if integrity.get("is_dev_mode"):
        risk_score = max(risk_score, 0.3)
        reason_codes.append("ENV_DEV_MODE")
        breakdown["dev_mode"] = "ENABLED - Developer options active"

    if integrity.get("is_usb_debug"):
        risk_score = max(risk_score, 0.4)
        reason_codes.append("ENV_USB_DEBUG")
        breakdown["usb_debug"] = "ENABLED - ADB debugging active"

    # If no flags, it's clean
    if not reason_codes:
        breakdown["status"] = "CLEAN - No integrity issues detected"

    return {
        "score": round(risk_score, 3),
        "reason_codes": reason_codes,
        "breakdown": breakdown,
        "is_compromised": risk_score > 0.8,
    }


def score_lightsync(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate light-sync injection risk score.
    Analyzes physics-based verification results to detect screen injection attacks.

    Args:
        bundle: Session bundle containing lightsync signals

    Returns:
        Score (0-1 where 1=highest risk), reason_codes list, and analysis details
    """
    ls = bundle.get("lightsync", {})

    # Extract values with defaults
    raw_score = ls.get("score", 0.5)  # Higher = more confident real
    quality = ls.get("quality", 0.5)
    rounds_passed = ls.get("rounds_passed", 0)
    rounds_total = ls.get("rounds_total", 3)

    reason_codes: List[str] = []
    details = {
        "raw_score": raw_score,
        "quality": quality,
        "rounds_passed": rounds_passed,
        "rounds_total": rounds_total,
    }

    # Calculate pass rate
    pass_rate = rounds_passed / max(rounds_total, 1)
    details["pass_rate"] = round(pass_rate, 2)

    # Risk assessment
    if rounds_passed == 0:
        # Complete failure - highly suspicious
        risk_score = 0.95
        reason_codes.append("LS_FAIL")
        details["analysis"] = "FAIL - No rounds passed, injection attack likely"
    elif pass_rate < 0.5:
        # Partial failure
        risk_score = 0.75
        reason_codes.append("LS_PARTIAL_FAIL")
        details["analysis"] = "SUSPICIOUS - Less than half rounds passed"
    elif quality < 0.4:
        # Poor quality capture
        risk_score = 0.6
        reason_codes.append("LS_LOW_QUALITY")
        details["analysis"] = "WARNING - Low capture quality, may need retry"
    elif raw_score < 0.5:
        # Low confidence
        risk_score = 0.5
        reason_codes.append("LS_SUSPICIOUS")
        details["analysis"] = "WARNING - Low reflection confidence"
    else:
        # Good result
        risk_score = 1.0 - (raw_score * pass_rate * 0.9)  # Inverse: high score = low risk
        risk_score = max(0.05, risk_score)  # Minimum baseline risk
        details["analysis"] = "PASS - Physics-based verification successful"

    return {
        "score": round(min(risk_score, 1.0), 3),
        "reason_codes": reason_codes,
        "details": details,
        "is_injection_likely": risk_score > 0.7,
    }


def score_liveness(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate face liveness/spoofing risk score.
    Uses AI model confidence and probability outputs.

    Args:
        bundle: Session bundle containing liveness signals

    Returns:
        Score (0-1 where 1=highest risk), reason_codes list, and model outputs
    """
    live = bundle.get("liveness", {})

    is_real = live.get("is_real", False)
    score = live.get("score", 0.5)  # Real probability
    quality = live.get("quality", 0.5)
    probabilities = live.get("probabilities", {})

    reason_codes: List[str] = []
    details = {
        "is_real": is_real,
        "confidence": round(score, 3),
        "quality": round(quality, 3),
        "probabilities": probabilities,
    }

    # Risk assessment
    if not is_real:
        risk_score = 0.95
        reason_codes.append("LIVENESS_FAIL")
        details["analysis"] = "FAIL - AI detected spoof/fake face"
    elif score < 0.5:
        risk_score = 0.8
        reason_codes.append("LIVENESS_LOW_CONF")
        details["analysis"] = "SUSPICIOUS - Very low real probability"
    elif score < 0.7:
        risk_score = 0.6
        reason_codes.append("LIVENESS_BORDERLINE")
        details["analysis"] = "WARNING - Borderline real probability"
    elif quality < 0.5:
        risk_score = 0.4
        reason_codes.append("LIVENESS_LOW_QUALITY")
        details["analysis"] = "WARNING - Low image quality"
    else:
        # Good result - invert score (high real prob = low risk)
        risk_score = 1.0 - score
        risk_score = max(0.05, risk_score)
        details["analysis"] = "PASS - Real face detected with high confidence"

    return {
        "score": round(min(risk_score, 1.0), 3),
        "reason_codes": reason_codes,
        "details": details,
        "is_spoof_likely": risk_score > 0.6,
    }


def score_behavior(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate behavioral biometrics risk score (mock for demo).
    Simulates analysis of typing patterns, swipe dynamics, device motion.

    In production: Compare session embedding to user's baseline.

    Args:
        bundle: Session bundle containing behavior signals

    Returns:
        Score (0-1 where 1=highest risk), reason_codes list, and behavioral indicators
    """
    behavior = bundle.get("behavior_demo", {})

    anomaly_score = behavior.get("anomaly_score", 0.1)
    risk_indicators = behavior.get("risk_indicators", [])
    feature_stats = behavior.get("feature_stats", {})

    reason_codes: List[str] = []
    details = {
        "anomaly_score": round(anomaly_score, 3),
        "feature_stats": feature_stats,
        "indicators_found": len(risk_indicators),
    }

    # Process risk indicators
    risk_score = anomaly_score

    for indicator in risk_indicators:
        if indicator == "typing_anomaly":
            risk_score = max(risk_score, 0.6)
            reason_codes.append("BEHAV_TYPING")
            details["typing"] = "ANOMALY - Typing pattern differs from baseline"
        elif indicator == "swipe_anomaly":
            risk_score = max(risk_score, 0.5)
            reason_codes.append("BEHAV_SWIPE")
            details["swipe"] = "ANOMALY - Touch/swipe pattern differs"
        elif indicator == "session_anomaly":
            risk_score = max(risk_score, 0.7)
            reason_codes.append("BEHAV_SESSION")
            details["session"] = "ANOMALY - Session behavior inconsistent"
        elif indicator == "device_anomaly":
            risk_score = max(risk_score, 0.4)
            reason_codes.append("BEHAV_DEVICE")
            details["device"] = "WARNING - Device usage pattern unusual"

    # If no indicators and low anomaly score
    if not reason_codes and anomaly_score < 0.3:
        details["analysis"] = "PASS - Behavior consistent with owner"
    elif not reason_codes:
        details["analysis"] = "WARNING - Elevated anomaly score"
        reason_codes.append("BEHAV_ELEVATED")
    else:
        details["analysis"] = "ALERT - Multiple behavioral anomalies detected"

    return {
        "score": round(min(risk_score, 1.0), 3),
        "reason_codes": reason_codes,
        "details": details,
        "is_anomalous": risk_score > 0.5,
        "is_mock": True,  # Flag that this is demo/mock data
    }


def score_context(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate transaction context risk score.
    Analyzes new payee, amount, device age, etc.

    Args:
        bundle: Session bundle containing transaction context

    Returns:
        Score (0-1 where 1=highest risk), reason_codes list, and context breakdown
    """
    ctx = bundle.get("txn_context", {})

    new_payee = ctx.get("new_payee", False)
    amount = ctx.get("amount", 0)
    amount_zscore = ctx.get("amount_zscore", 0)
    device_age_days = ctx.get("device_age_days", 30)
    ip_risk = ctx.get("ip_risk", 0)

    reason_codes: List[str] = []
    risk_score = 0.0
    details = {}

    # New payee risk
    if new_payee:
        reason_codes.append("CONTEXT_NEW_PAYEE")
        risk_score = max(risk_score, 0.3)
        details["payee"] = "NEW - First time recipient"

        # Compound risk for high value + new payee
        if amount > 10000:
            reason_codes.append("CONTEXT_HIGH_VALUE")
            risk_score = max(risk_score, 0.6)
            details["amount"] = f"HIGH - {amount} to new payee"
        elif amount > 5000:
            risk_score = max(risk_score, 0.45)
            details["amount"] = f"ELEVATED - {amount} to new payee"

    # Amount anomaly
    if amount_zscore > 2.0:
        reason_codes.append("CONTEXT_AMOUNT_ANOMALY")
        risk_score = max(risk_score, 0.5)
        details["amount_pattern"] = f"ANOMALY - {amount_zscore:.1f} std from average"

    # New device
    if device_age_days < 1:
        reason_codes.append("CONTEXT_NEW_DEVICE")
        risk_score = max(risk_score, 0.4)
        details["device"] = "NEW - First day on this device"
    elif device_age_days < 7:
        risk_score = max(risk_score, 0.2)
        details["device"] = f"RECENT - Device age {device_age_days} days"

    # IP risk
    if ip_risk > 0.5:
        reason_codes.append("CONTEXT_IP_RISK")
        risk_score = max(risk_score, ip_risk * 0.8)
        details["ip"] = f"RISK - IP risk score {ip_risk:.2f}"

    if not reason_codes:
        details["analysis"] = "NORMAL - Standard transaction context"
    else:
        details["analysis"] = "ELEVATED - Context risk factors present"

    return {
        "score": round(min(risk_score, 1.0), 3),
        "reason_codes": reason_codes,
        "details": details,
        "is_high_risk": risk_score > 0.5,
    }
