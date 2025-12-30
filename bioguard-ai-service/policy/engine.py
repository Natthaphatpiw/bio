"""
Policy Engine - Hard guardrails that agent MUST respect

The Policy Engine enforces non-negotiable security rules.
Agent can only make decisions AT OR ABOVE the policy floor.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Callable, Optional
from enum import Enum


class ActionLevel(Enum):
    """Decision action levels in order of severity"""
    ALLOW = 0
    STEP_UP = 1
    HOLD = 2
    BLOCK = 3


@dataclass
class PolicyResult:
    """Result of policy evaluation"""
    min_action: str  # ALLOW, STEP_UP, HOLD, BLOCK
    triggered_rules: List[str]
    risk_floor: float = 0.0


class PolicyEngine:
    """
    Deterministic policy engine with hard guardrails.
    Agent MUST respect these constraints.

    Rules are evaluated in priority order (lower = higher priority).
    The highest action level from all triggered rules becomes the floor.
    """

    def __init__(self):
        self.rules = self._load_default_rules()

    def _load_default_rules(self) -> List[Dict]:
        """
        Load default policy rules.
        In production, load from database for hot-reloading.
        """
        return [
            # === BLOCK Rules (Priority 1-9) - Non-negotiable ===
            {
                "name": "BLOCK_HOOKING",
                "description": "Block if Frida/Xposed hooking detected",
                "condition": self._check_hooking,
                "action": ActionLevel.BLOCK,
                "priority": 1,
            },
            {
                "name": "BLOCK_EMULATOR_EKYC",
                "description": "Block emulator for eKYC verification",
                "condition": self._check_emulator_ekyc,
                "action": ActionLevel.BLOCK,
                "priority": 2,
            },
            {
                "name": "BLOCK_LIGHTSYNC_CRITICAL",
                "description": "Block if light-sync completely fails with hooking signals",
                "condition": self._check_lightsync_critical,
                "action": ActionLevel.BLOCK,
                "priority": 3,
            },

            # === HOLD Rules (Priority 10-19) - Require manual review ===
            {
                "name": "HOLD_ROOTED_HIGH_VALUE",
                "description": "Hold rooted device with high-value transaction",
                "condition": self._check_rooted_high_value,
                "action": ActionLevel.HOLD,
                "priority": 10,
            },
            {
                "name": "HOLD_LIVENESS_FAIL",
                "description": "Hold if liveness check fails completely",
                "condition": self._check_liveness_fail,
                "action": ActionLevel.HOLD,
                "priority": 11,
            },
            {
                "name": "HOLD_MULTI_SIGNAL_FAIL",
                "description": "Hold if multiple signal domains fail",
                "condition": self._check_multi_signal_fail,
                "action": ActionLevel.HOLD,
                "priority": 12,
            },

            # === STEP_UP Rules (Priority 20-29) - Require additional verification ===
            {
                "name": "STEPUP_NEW_PAYEE_HIGH",
                "description": "Step-up for high-value transfer to new payee",
                "condition": self._check_new_payee_high,
                "action": ActionLevel.STEP_UP,
                "priority": 20,
            },
            {
                "name": "STEPUP_ROOTED_DEVICE",
                "description": "Step-up for any rooted device",
                "condition": self._check_rooted,
                "action": ActionLevel.STEP_UP,
                "priority": 21,
            },
            {
                "name": "STEPUP_BEHAVIOR_ANOMALY",
                "description": "Step-up if behavioral biometrics anomaly detected",
                "condition": self._check_behavior_anomaly,
                "action": ActionLevel.STEP_UP,
                "priority": 22,
            },
            {
                "name": "STEPUP_LIGHTSYNC_SUSPICIOUS",
                "description": "Step-up if light-sync is suspicious",
                "condition": self._check_lightsync_suspicious,
                "action": ActionLevel.STEP_UP,
                "priority": 23,
            },
        ]

    def evaluate(self, bundle: Dict, scores: Dict) -> PolicyResult:
        """
        Evaluate all rules and return highest min_action.

        Args:
            bundle: Session bundle with all signals
            scores: Dictionary of scores from scoring tools

        Returns:
            PolicyResult with min_action and triggered_rules
        """
        triggered = []
        max_action = ActionLevel.ALLOW
        max_risk = 0.0

        # Sort rules by priority and evaluate
        for rule in sorted(self.rules, key=lambda r: r["priority"]):
            try:
                if rule["condition"](bundle, scores):
                    triggered.append(rule["name"])
                    if rule["action"].value > max_action.value:
                        max_action = rule["action"]
                        # Set risk floor based on action
                        if max_action == ActionLevel.BLOCK:
                            max_risk = 0.95
                        elif max_action == ActionLevel.HOLD:
                            max_risk = 0.8
                        elif max_action == ActionLevel.STEP_UP:
                            max_risk = 0.5
            except Exception as e:
                # Log but don't fail on rule evaluation errors
                print(f"Rule {rule['name']} evaluation error: {e}")
                continue

        return PolicyResult(
            min_action=max_action.name,
            triggered_rules=triggered,
            risk_floor=max_risk,
        )

    # === Rule Condition Functions ===

    def _check_hooking(self, bundle: Dict, scores: Dict) -> bool:
        """Check if hooking detected"""
        integrity = bundle.get("integrity", {})
        return integrity.get("is_hooking", False)

    def _check_emulator_ekyc(self, bundle: Dict, scores: Dict) -> bool:
        """Check if emulator + eKYC event"""
        integrity = bundle.get("integrity", {})
        event_type = bundle.get("event_type", "")
        return integrity.get("is_emulator", False) and event_type == "EKYC"

    def _check_lightsync_critical(self, bundle: Dict, scores: Dict) -> bool:
        """Check if light-sync critically failed with integrity issues"""
        integrity = bundle.get("integrity", {})
        ls_score = scores.get("lightsync", {}).get("score", 0)

        # Block if LS fails AND any integrity flag
        has_integrity_issue = (
            integrity.get("is_hooking") or
            integrity.get("is_emulator") or
            integrity.get("is_rooted")
        )
        return ls_score > 0.9 and has_integrity_issue

    def _check_rooted_high_value(self, bundle: Dict, scores: Dict) -> bool:
        """Check if rooted device + high value transaction"""
        integrity = bundle.get("integrity", {})
        txn = bundle.get("txn_context", {})
        return integrity.get("is_rooted", False) and txn.get("amount", 0) > 10000

    def _check_liveness_fail(self, bundle: Dict, scores: Dict) -> bool:
        """Check if liveness completely failed"""
        liveness_score = scores.get("liveness", {}).get("score", 0)
        return liveness_score > 0.9

    def _check_multi_signal_fail(self, bundle: Dict, scores: Dict) -> bool:
        """Check if multiple signals failed (2+ domains with score > 0.7)"""
        high_risk_count = 0
        for domain in ["integrity", "lightsync", "liveness", "behavior"]:
            if scores.get(domain, {}).get("score", 0) > 0.7:
                high_risk_count += 1
        return high_risk_count >= 2

    def _check_new_payee_high(self, bundle: Dict, scores: Dict) -> bool:
        """Check if high-value to new payee"""
        txn = bundle.get("txn_context", {})
        return txn.get("new_payee", False) and txn.get("amount", 0) > 5000

    def _check_rooted(self, bundle: Dict, scores: Dict) -> bool:
        """Check if device is rooted"""
        integrity = bundle.get("integrity", {})
        return integrity.get("is_rooted", False)

    def _check_behavior_anomaly(self, bundle: Dict, scores: Dict) -> bool:
        """Check if behavioral biometrics anomaly"""
        behavior_score = scores.get("behavior", {}).get("score", 0)
        return behavior_score > 0.6

    def _check_lightsync_suspicious(self, bundle: Dict, scores: Dict) -> bool:
        """Check if light-sync suspicious but not critical"""
        ls_score = scores.get("lightsync", {}).get("score", 0)
        return 0.5 < ls_score < 0.9
