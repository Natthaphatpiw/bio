"""
Policy Tools - Hard guardrails that agent MUST respect
"""
from typing import Dict, Any, List


def policy_floor(bundle: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply hard policy rules that agent MUST respect.
    Returns minimum required action that cannot be lowered.

    The policy floor ensures critical security rules are enforced
    regardless of agent's adaptive decision making.

    Args:
        bundle: Session bundle with all signals
        scores: Dictionary of scores from scoring tools
            Expected keys: integrity, lightsync, liveness, behavior, context

    Returns:
        min_action: ALLOW, STEP_UP, HOLD, or BLOCK
        triggered_rules: List of rule names that fired
        risk_floor: Minimum risk score implied by the policy floor
        can_allow: Boolean - can agent decide ALLOW?
        must_block: Boolean - must agent decide BLOCK?
    """
    from policy.engine import PolicyEngine

    engine = PolicyEngine()
    result = engine.evaluate(bundle, scores)

    return {
        "min_action": result.min_action,
        "triggered_rules": result.triggered_rules,
        "risk_floor": result.risk_floor,
        "can_allow": result.min_action == "ALLOW",
        "must_stepup": result.min_action == "STEP_UP",
        "must_hold": result.min_action in ["HOLD", "BLOCK"],
        "must_block": result.min_action == "BLOCK",
    }


def get_policy_rules() -> List[Dict[str, Any]]:
    """
    Get list of active policy rules for reference.

    Returns:
        List of rule definitions with name, description, and action
    """
    from policy.engine import PolicyEngine

    engine = PolicyEngine()
    return [
        {
            "name": rule["name"],
            "description": rule.get("description", ""),
            "action": rule["action"].name,
            "priority": rule["priority"],
        }
        for rule in engine.rules
    ]
