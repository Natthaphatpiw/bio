"""
Case Tools - Create and manage fraud investigation cases
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid


# In-memory case storage for demo
_cases: Dict[str, Dict[str, Any]] = {}


def create_case(
    session_id: str,
    summary: str,
    severity: str,
    evidence_refs: List[str],
    recommended_action: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a fraud investigation case for ops review.

    Args:
        session_id: The session that triggered the case
        summary: AI-generated summary of the suspicious activity
        severity: LOW, MEDIUM, HIGH, or CRITICAL
        evidence_refs: List of signal/decision IDs as evidence
        recommended_action: Optional recommended resolution

    Returns:
        Created case ID and status
    """
    case_id = f"case_{uuid.uuid4().hex[:12]}"

    case = {
        "id": case_id,
        "session_id": session_id,
        "status": "OPEN",
        "severity": severity.upper(),
        "summary": summary,
        "evidence_refs": evidence_refs,
        "recommended_action": recommended_action,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "timeline": [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "event": "Case created by AI Agent",
                "actor": "system",
                "details": {
                    "recommended_action": recommended_action,
                    "auto_created": True,
                }
            }
        ],
        "assigned_to": None,
        "resolution": None,
        "notes": [],
    }

    _cases[case_id] = case

    return {
        "case_id": case_id,
        "status": "OPEN",
        "severity": severity.upper(),
        "created": True,
        "message": f"Case {case_id} created for session {session_id}",
    }


def get_case(case_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a fraud case by ID.

    Args:
        case_id: The case identifier

    Returns:
        Case data or None if not found
    """
    return _cases.get(case_id)


def get_cases_by_session(session_id: str) -> List[Dict[str, Any]]:
    """
    Get all cases for a session.

    Args:
        session_id: The session identifier

    Returns:
        List of cases for the session
    """
    return [
        case for case in _cases.values()
        if case["session_id"] == session_id
    ]


def list_cases(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    List fraud cases with optional filters.

    Args:
        status: Filter by status (OPEN, INVESTIGATING, etc.)
        severity: Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)
        limit: Maximum number of cases to return

    Returns:
        List of matching cases
    """
    cases = list(_cases.values())

    if status:
        cases = [c for c in cases if c["status"] == status.upper()]

    if severity:
        cases = [c for c in cases if c["severity"] == severity.upper()]

    # Sort by created_at descending
    cases.sort(key=lambda c: c["created_at"], reverse=True)

    return cases[:limit]


def update_case_status(
    case_id: str,
    status: str,
    actor: str = "system",
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update a case's status.

    Args:
        case_id: The case identifier
        status: New status (OPEN, INVESTIGATING, CONFIRMED_FRAUD, FALSE_POSITIVE, CLOSED)
        actor: Who made the change
        notes: Optional notes about the status change

    Returns:
        Updated case or error
    """
    case = _cases.get(case_id)
    if not case:
        return {"error": f"Case {case_id} not found"}

    old_status = case["status"]
    case["status"] = status.upper()
    case["updated_at"] = datetime.utcnow().isoformat()

    timeline_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": f"Status changed from {old_status} to {status.upper()}",
        "actor": actor,
        "details": {"notes": notes} if notes else {},
    }
    case["timeline"].append(timeline_event)

    if notes:
        case["notes"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "author": actor,
            "content": notes,
        })

    return {
        "case_id": case_id,
        "status": case["status"],
        "updated": True,
    }


def add_case_comment(
    case_id: str,
    author: str,
    content: str,
    is_ai_generated: bool = False
) -> Dict[str, Any]:
    """
    Add a comment to a case.

    Args:
        case_id: The case identifier
        author: Who wrote the comment
        content: Comment content
        is_ai_generated: Whether the comment was AI-generated

    Returns:
        Result of the operation
    """
    case = _cases.get(case_id)
    if not case:
        return {"error": f"Case {case_id} not found"}

    comment = {
        "id": f"comment_{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.utcnow().isoformat(),
        "author": author,
        "content": content,
        "is_ai_generated": is_ai_generated,
    }

    case["notes"].append(comment)
    case["updated_at"] = datetime.utcnow().isoformat()

    return {
        "case_id": case_id,
        "comment_id": comment["id"],
        "added": True,
    }


def summarize_case_timeline(case_id: str) -> Dict[str, Any]:
    """
    Generate a summary of case timeline for ops review.

    Args:
        case_id: The case identifier

    Returns:
        Timeline summary with key events
    """
    case = _cases.get(case_id)
    if not case:
        return {"error": f"Case {case_id} not found"}

    return {
        "case_id": case_id,
        "status": case["status"],
        "severity": case["severity"],
        "summary": case["summary"],
        "timeline": case["timeline"],
        "timeline_count": len(case["timeline"]),
        "notes_count": len(case["notes"]),
        "evidence_count": len(case["evidence_refs"]),
        "created_at": case["created_at"],
        "updated_at": case["updated_at"],
    }


# Utility functions for demo
def clear_cases() -> None:
    """Clear all cases (for testing)"""
    _cases.clear()


def get_case_count() -> int:
    """Get total case count"""
    return len(_cases)
