"""
In-Memory Feature Store - For demo and testing
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

from .feature_store import FeatureStore
from models.bundles import SessionBundle, StoredSignal, StoredDecision
from models.events import SessionEvent, EventType


class InMemoryFeatureStore(FeatureStore):
    """
    In-memory implementation of feature store.
    Suitable for demo/hackathon. Replace with Redis for production.
    """

    def __init__(self):
        self._bundles: Dict[str, SessionBundle] = {}
        self._signals: Dict[str, List[StoredSignal]] = {}
        self._decisions: Dict[str, StoredDecision] = {}
        self._lock = asyncio.Lock()

    async def store_event(self, event: SessionEvent) -> None:
        """Store a session event and create a bundle"""
        async with self._lock:
            bundle = SessionBundle.from_event(event)
            self._bundles[event.session_id] = bundle

            # Also store individual signals
            if event.integrity:
                await self._store_signal_internal(
                    event.session_id, "integrity", event.integrity.model_dump()
                )
            if event.lightsync:
                await self._store_signal_internal(
                    event.session_id, "lightsync", event.lightsync.model_dump()
                )
            if event.liveness:
                await self._store_signal_internal(
                    event.session_id, "liveness", event.liveness.model_dump()
                )
            if event.behavior_demo:
                await self._store_signal_internal(
                    event.session_id, "behavior", event.behavior_demo.model_dump()
                )
            if event.txn_context:
                await self._store_signal_internal(
                    event.session_id, "context", event.txn_context.model_dump()
                )

    async def _store_signal_internal(
        self, session_id: str, signal_type: str, raw_data: Dict[str, Any]
    ) -> None:
        """Internal helper to store signal without lock"""
        signal = StoredSignal(
            session_id=session_id,
            signal_type=signal_type,
            raw_data=raw_data,
        )
        if session_id not in self._signals:
            self._signals[session_id] = []

        # Replace existing signal of same type
        self._signals[session_id] = [
            s for s in self._signals[session_id] if s.signal_type != signal_type
        ]
        self._signals[session_id].append(signal)

    async def get_bundle(self, session_id: str) -> Optional[SessionBundle]:
        """Get aggregated bundle for a session"""
        async with self._lock:
            return self._bundles.get(session_id)

    async def store_signal(self, signal: StoredSignal) -> None:
        """Store an individual signal"""
        async with self._lock:
            await self._store_signal_internal(
                signal.session_id, signal.signal_type, signal.raw_data
            )

    async def get_signals(self, session_id: str) -> List[StoredSignal]:
        """Get all signals for a session"""
        async with self._lock:
            return self._signals.get(session_id, [])

    async def store_decision(self, decision: StoredDecision) -> None:
        """Store an agent decision"""
        async with self._lock:
            self._decisions[decision.session_id] = decision

    async def get_decision(self, session_id: str) -> Optional[StoredDecision]:
        """Get the latest decision for a session"""
        async with self._lock:
            return self._decisions.get(session_id)

    async def update_score(
        self, session_id: str, signal_type: str, score: float, reason_codes: List[str]
    ) -> None:
        """Update processed score for a signal"""
        async with self._lock:
            signals = self._signals.get(session_id, [])
            for signal in signals:
                if signal.signal_type == signal_type:
                    signal.processed_score = score
                    signal.reason_codes = reason_codes
                    break

    # Demo/Testing helpers
    async def clear(self) -> None:
        """Clear all data (for testing)"""
        async with self._lock:
            self._bundles.clear()
            self._signals.clear()
            self._decisions.clear()

    async def list_sessions(self) -> List[str]:
        """List all session IDs (for debugging)"""
        async with self._lock:
            return list(self._bundles.keys())

    async def create_demo_session(
        self,
        session_id: str,
        scenario: str = "clean"
    ) -> SessionBundle:
        """
        Create a demo session for testing
        Scenarios: clean, injection, ato, rooted
        """
        from models.events import (
            IntegritySignal, LightSyncSignal, LivenessSignal,
            BehaviorSignal, TransactionContext
        )

        scenarios = {
            "clean": {
                "integrity": IntegritySignal(
                    is_emulator=False, is_rooted=False, is_hooking=False
                ),
                "lightsync": LightSyncSignal(
                    score=0.85, quality=0.76, rounds_passed=3, rounds_total=3
                ),
                "liveness": LivenessSignal(
                    score=0.92, quality=0.8, is_real=True
                ),
                "behavior": BehaviorSignal(anomaly_score=0.1),
                "context": TransactionContext(new_payee=False, amount=500),
            },
            "injection": {
                "integrity": IntegritySignal(
                    is_emulator=False, is_rooted=False, is_hooking=True
                ),
                "lightsync": LightSyncSignal(
                    score=0.15, quality=0.2, rounds_passed=0, rounds_total=3
                ),
                "liveness": LivenessSignal(
                    score=0.65, quality=0.5, is_real=True
                ),
                "behavior": BehaviorSignal(anomaly_score=0.2),
                "context": TransactionContext(new_payee=False, amount=1000),
            },
            "ato": {
                "integrity": IntegritySignal(
                    is_emulator=False, is_rooted=False, is_hooking=False
                ),
                "lightsync": LightSyncSignal(
                    score=0.8, quality=0.7, rounds_passed=3, rounds_total=3
                ),
                "liveness": LivenessSignal(
                    score=0.88, quality=0.75, is_real=True
                ),
                "behavior": BehaviorSignal(
                    anomaly_score=0.75,
                    risk_indicators=["session_anomaly", "typing_anomaly"]
                ),
                "context": TransactionContext(new_payee=True, amount=25000),
            },
            "rooted": {
                "integrity": IntegritySignal(
                    is_emulator=False, is_rooted=True, is_hooking=False
                ),
                "lightsync": LightSyncSignal(
                    score=0.8, quality=0.7, rounds_passed=2, rounds_total=3
                ),
                "liveness": LivenessSignal(
                    score=0.85, quality=0.7, is_real=True
                ),
                "behavior": BehaviorSignal(anomaly_score=0.3),
                "context": TransactionContext(new_payee=True, amount=15000),
            },
        }

        scenario_data = scenarios.get(scenario, scenarios["clean"])

        event = SessionEvent(
            session_id=session_id,
            event_type=EventType.TRANSFER,
            integrity=scenario_data["integrity"],
            lightsync=scenario_data["lightsync"],
            liveness=scenario_data["liveness"],
            behavior_demo=scenario_data["behavior"],
            txn_context=scenario_data["context"],
        )

        await self.store_event(event)
        return await self.get_bundle(session_id)
