"""
Notification Tools - Dashboard and user notifications
"""
from typing import Dict, Any, Optional
from datetime import datetime
import json


# In-memory notification log for demo
_notifications: list = []


def notify_dashboard(
    session_id: str,
    decision: str,
    final_risk: float,
    reason_codes: list,
    explanation: str,
    case_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send notification to dashboard for real-time updates.
    In production: Use WebSocket/Supabase Realtime/Pusher.

    Args:
        session_id: The session that was decided
        decision: ALLOW, STEP_UP, HOLD, or BLOCK
        final_risk: Risk score 0-1
        reason_codes: List of reason codes
        explanation: Human-readable explanation
        case_id: Optional case ID if case was created

    Returns:
        Notification status
    """
    notification = {
        "type": "agent_decision",
        "session_id": session_id,
        "decision": decision,
        "final_risk": final_risk,
        "reason_codes": reason_codes,
        "explanation": explanation,
        "case_id": case_id,
        "timestamp": datetime.utcnow().isoformat(),
    }

    _notifications.append(notification)

    # In production: Send to Supabase Realtime or WebSocket
    # await supabase.from_('agent_decisions').insert(notification)

    return {
        "sent": True,
        "channel": "dashboard",
        "notification_type": "agent_decision",
        "session_id": session_id,
    }


def send_user_message(
    session_id: str,
    message_type: str,
    message: str,
    action_required: bool = False,
    retry_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send message to user device/app.
    In production: Use push notification/in-app messaging.

    Args:
        session_id: The session for the user
        message_type: Type of message (info, warning, action_required)
        message: User-friendly message content
        action_required: Whether user needs to take action
        retry_url: Optional URL for retry flow

    Returns:
        Message delivery status
    """
    user_notification = {
        "type": "user_message",
        "session_id": session_id,
        "message_type": message_type,
        "message": message,
        "action_required": action_required,
        "retry_url": retry_url,
        "timestamp": datetime.utcnow().isoformat(),
    }

    _notifications.append(user_notification)

    # In production: Send push notification or update mobile app state

    return {
        "sent": True,
        "channel": "mobile",
        "message_type": message_type,
        "session_id": session_id,
    }


def send_webhook(
    webhook_url: str,
    session_id: str,
    event_type: str,
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send webhook to merchant endpoint.
    In production: Use async HTTP client with retry logic.

    Args:
        webhook_url: Merchant's webhook URL
        session_id: The session ID
        event_type: Type of event (verification.completed, etc.)
        payload: Event payload

    Returns:
        Webhook delivery status
    """
    webhook_notification = {
        "type": "webhook",
        "webhook_url": webhook_url,
        "session_id": session_id,
        "event_type": event_type,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat(),
    }

    _notifications.append(webhook_notification)

    # In production: Use httpx/aiohttp with retry
    # try:
    #     async with httpx.AsyncClient() as client:
    #         response = await client.post(webhook_url, json=payload, timeout=10)
    #         return {"sent": True, "status_code": response.status_code}
    # except Exception as e:
    #     return {"sent": False, "error": str(e)}

    return {
        "sent": True,
        "channel": "webhook",
        "event_type": event_type,
        "session_id": session_id,
        "webhook_url": webhook_url,
    }


def get_notifications(
    session_id: Optional[str] = None,
    notification_type: Optional[str] = None,
    limit: int = 50
) -> list:
    """
    Get notification history (for debugging/demo).

    Args:
        session_id: Filter by session
        notification_type: Filter by type
        limit: Maximum number to return

    Returns:
        List of notifications
    """
    result = _notifications.copy()

    if session_id:
        result = [n for n in result if n.get("session_id") == session_id]

    if notification_type:
        result = [n for n in result if n.get("type") == notification_type]

    result.sort(key=lambda n: n.get("timestamp", ""), reverse=True)

    return result[:limit]


def clear_notifications() -> None:
    """Clear notification history (for testing)"""
    _notifications.clear()


def get_notification_count() -> int:
    """Get total notification count"""
    return len(_notifications)
