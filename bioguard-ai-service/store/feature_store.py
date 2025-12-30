"""
Feature Store - Abstract interface for session data storage
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from models.bundles import SessionBundle, StoredSignal, StoredDecision
from models.events import SessionEvent


class FeatureStore(ABC):
    """
    Abstract feature store interface.
    Implementations: InMemoryFeatureStore (demo), RedisFeatureStore (production)
    """

    @abstractmethod
    async def store_event(self, event: SessionEvent) -> None:
        """Store a session event and all its signals"""
        pass

    @abstractmethod
    async def get_bundle(self, session_id: str) -> Optional[SessionBundle]:
        """Get aggregated bundle for a session"""
        pass

    @abstractmethod
    async def store_signal(self, signal: StoredSignal) -> None:
        """Store an individual signal"""
        pass

    @abstractmethod
    async def get_signals(self, session_id: str) -> List[StoredSignal]:
        """Get all signals for a session"""
        pass

    @abstractmethod
    async def store_decision(self, decision: StoredDecision) -> None:
        """Store an agent decision"""
        pass

    @abstractmethod
    async def get_decision(self, session_id: str) -> Optional[StoredDecision]:
        """Get the latest decision for a session"""
        pass

    @abstractmethod
    async def update_score(
        self, session_id: str, signal_type: str, score: float, reason_codes: List[str]
    ) -> None:
        """Update processed score for a signal"""
        pass


# Global feature store instance
_feature_store: Optional[FeatureStore] = None


def get_feature_store() -> FeatureStore:
    """Get the global feature store instance"""
    global _feature_store
    if _feature_store is None:
        # Default to in-memory store for demo
        from .memory_store import InMemoryFeatureStore
        _feature_store = InMemoryFeatureStore()
    return _feature_store


def set_feature_store(store: FeatureStore) -> None:
    """Set the global feature store instance"""
    global _feature_store
    _feature_store = store
