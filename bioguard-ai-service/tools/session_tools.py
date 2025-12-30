"""
Session Tools - Fetch and manage session data
"""
from typing import Dict, Any, Optional


def get_session_bundle(session_id: str) -> Dict[str, Any]:
    """
    Fetch all signals for a session from the feature store.
    Returns a bundle with integrity, lightsync, liveness, behavior, and context signals.

    Args:
        session_id: The unique session identifier

    Returns:
        Dictionary containing all available signals for the session, or error if not found
    """
    from store.feature_store import get_feature_store
    import asyncio

    async def _fetch():
        store = get_feature_store()
        bundle = await store.get_bundle(session_id)
        if bundle:
            return bundle.to_dict()
        return {"error": f"Session {session_id} not found"}

    # Run async in sync context (for agent tool compatibility)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in async context, create task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _fetch())
                return future.result()
        else:
            return asyncio.run(_fetch())
    except RuntimeError:
        return asyncio.run(_fetch())


def get_session_status(session_id: str) -> Dict[str, Any]:
    """
    Get the current status of a session including any existing decision.

    Args:
        session_id: The unique session identifier

    Returns:
        Dictionary with session status and decision if available
    """
    from store.feature_store import get_feature_store
    import asyncio

    async def _fetch():
        store = get_feature_store()
        bundle = await store.get_bundle(session_id)
        decision = await store.get_decision(session_id)

        if not bundle:
            return {"error": f"Session {session_id} not found"}

        result = {
            "session_id": session_id,
            "event_type": bundle.event_type.value if bundle.event_type else None,
            "has_signals": True,
            "has_decision": decision is not None,
        }

        if decision:
            result["decision"] = decision.decision
            result["final_risk"] = decision.final_risk

        return result

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _fetch())
                return future.result()
        else:
            return asyncio.run(_fetch())
    except RuntimeError:
        return asyncio.run(_fetch())
