"""
Cases Router - Fraud case management endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime

from tools.case_tools import (
    get_case,
    get_cases_by_session,
    list_cases,
    update_case_status,
    add_case_comment,
    summarize_case_timeline,
)

router = APIRouter(prefix="/cases", tags=["cases"])


class CaseUpdateRequest(BaseModel):
    """Request to update case status"""
    status: str  # OPEN, INVESTIGATING, CONFIRMED_FRAUD, FALSE_POSITIVE, CLOSED
    actor: str = "ops_user"
    notes: Optional[str] = None


class CaseCommentRequest(BaseModel):
    """Request to add a comment to a case"""
    author: str
    content: str
    is_ai_generated: bool = False


class CopilotChatRequest(BaseModel):
    """Request to chat with fraud copilot about a case"""
    message: str
    context: Optional[Dict[str, Any]] = None


class CopilotChatResponse(BaseModel):
    """Response from fraud copilot"""
    response: str
    suggested_actions: List[str] = []
    confidence: float = 0.0
    sources: List[str] = []


@router.get("/")
async def get_cases(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
):
    """
    List fraud cases with optional filters.
    """
    cases = list_cases(status=status, severity=severity, limit=limit)
    return {
        "cases": cases,
        "total": len(cases),
        "filters": {
            "status": status,
            "severity": severity,
        }
    }


@router.get("/{case_id}")
async def get_case_detail(case_id: str):
    """
    Get detailed information about a specific case.
    """
    case = get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=404,
            detail=f"Case {case_id} not found"
        )
    return case


@router.get("/session/{session_id}")
async def get_cases_for_session(session_id: str):
    """
    Get all cases associated with a session.
    """
    cases = get_cases_by_session(session_id)
    return {
        "session_id": session_id,
        "cases": cases,
        "total": len(cases),
    }


@router.put("/{case_id}/status")
async def update_case(case_id: str, request: CaseUpdateRequest):
    """
    Update a case's status.
    """
    valid_statuses = ["OPEN", "INVESTIGATING", "CONFIRMED_FRAUD", "FALSE_POSITIVE", "CLOSED"]
    if request.status.upper() not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    result = update_case_status(
        case_id=case_id,
        status=request.status,
        actor=request.actor,
        notes=request.notes,
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.post("/{case_id}/comments")
async def add_comment(case_id: str, request: CaseCommentRequest):
    """
    Add a comment to a case.
    """
    result = add_case_comment(
        case_id=case_id,
        author=request.author,
        content=request.content,
        is_ai_generated=request.is_ai_generated,
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/{case_id}/timeline")
async def get_case_timeline(case_id: str):
    """
    Get a summary of the case timeline.
    """
    result = summarize_case_timeline(case_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.post("/{case_id}/chat", response_model=CopilotChatResponse)
async def chat_with_copilot(case_id: str, request: CopilotChatRequest):
    """
    Chat with the Fraud Copilot about a specific case.

    The copilot can:
    - Explain the decision and evidence
    - Suggest investigation steps
    - Compare with similar cases
    - Recommend resolution actions
    """
    # Get case data
    case = get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=404,
            detail=f"Case {case_id} not found"
        )

    # Import and run fraud copilot
    try:
        from bioguard_agents.fraud_copilot import run_fraud_copilot

        copilot_response = await run_fraud_copilot(
            case_id=case_id,
            case_data=case,
            user_message=request.message,
            context=request.context,
        )

        return CopilotChatResponse(
            response=copilot_response.get("response", "Unable to process request."),
            suggested_actions=copilot_response.get("suggested_actions", []),
            confidence=copilot_response.get("confidence", 0.0),
            sources=copilot_response.get("sources", []),
        )
    except ImportError:
        # Copilot not implemented yet, return mock response
        return CopilotChatResponse(
            response=_get_mock_copilot_response(case, request.message),
            suggested_actions=_get_mock_suggested_actions(case),
            confidence=0.85,
            sources=[f"case:{case_id}", f"session:{case.get('session_id', 'unknown')}"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Copilot error: {str(e)}"
        )


@router.get("/{case_id}/similar")
async def get_similar_cases(case_id: str, limit: int = 5):
    """
    Find similar cases for comparison.
    """
    case = get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=404,
            detail=f"Case {case_id} not found"
        )

    # Get all cases and find similar ones based on severity and evidence
    all_cases = list_cases(limit=100)
    similar = []

    for other_case in all_cases:
        if other_case["id"] == case_id:
            continue

        # Simple similarity: same severity or similar evidence
        similarity_score = 0.0

        if other_case["severity"] == case["severity"]:
            similarity_score += 0.3

        # Compare evidence refs (if any overlap)
        case_evidence = set(case.get("evidence_refs", []))
        other_evidence = set(other_case.get("evidence_refs", []))
        if case_evidence and other_evidence:
            overlap = len(case_evidence & other_evidence) / len(case_evidence | other_evidence)
            similarity_score += overlap * 0.5

        # Status-based similarity
        if other_case["status"] in ["CONFIRMED_FRAUD", "FALSE_POSITIVE"]:
            similarity_score += 0.2  # Resolved cases are more useful for comparison

        if similarity_score > 0.2:
            similar.append({
                "case_id": other_case["id"],
                "similarity_score": round(similarity_score, 2),
                "severity": other_case["severity"],
                "status": other_case["status"],
                "summary": other_case.get("summary", "")[:100],
            })

    # Sort by similarity and limit
    similar.sort(key=lambda x: x["similarity_score"], reverse=True)

    return {
        "case_id": case_id,
        "similar_cases": similar[:limit],
        "total_found": len(similar),
    }


def _get_mock_copilot_response(case: Dict, message: str) -> str:
    """Generate a mock copilot response for demo"""
    severity = case.get("severity", "MEDIUM")
    summary = case.get("summary", "Suspicious activity detected")

    message_lower = message.lower()

    if "explain" in message_lower or "why" in message_lower:
        return f"""Based on my analysis of case {case.get('id', 'unknown')}:

**Summary**: {summary}

**Key Findings**:
- Severity Level: {severity}
- The decision was made based on multiple signals indicating potential fraud risk
- The policy engine flagged this case for manual review

**Evidence Analysis**:
The session showed concerning patterns in the verification flow. I recommend reviewing the signal timeline and comparing with similar resolved cases."""

    elif "action" in message_lower or "recommend" in message_lower:
        if severity == "CRITICAL":
            return """For this CRITICAL severity case, I recommend:

1. **Immediate Action**: Block the account temporarily
2. **Investigation**: Review all recent transactions from this device
3. **Verification**: Contact the user through a verified channel
4. **Documentation**: Document all findings in the case timeline

Would you like me to draft a user notification message?"""
        else:
            return f"""For this {severity} severity case, I recommend:

1. **Review**: Examine the evidence timeline carefully
2. **Compare**: Look at similar resolved cases
3. **Decide**: Mark as either CONFIRMED_FRAUD or FALSE_POSITIVE

The evidence suggests a moderate confidence in fraud. Manual verification may help clarify."""

    elif "similar" in message_lower:
        return """I've analyzed similar cases in the system. Common patterns include:

- Device fingerprint anomalies
- LightSync verification failures
- Unusual transaction timing

Based on how similar cases were resolved, 70% were confirmed as fraud attempts."""

    else:
        return f"""I'm the Fraud Copilot assistant for case {case.get('id', 'unknown')}.

I can help you:
- **Explain** the decision and evidence
- **Recommend** investigation actions
- **Compare** with similar cases
- **Draft** user communications

What would you like to know about this case?"""


def _get_mock_suggested_actions(case: Dict) -> List[str]:
    """Get mock suggested actions based on case severity"""
    severity = case.get("severity", "MEDIUM")
    status = case.get("status", "OPEN")

    actions = []

    if status == "OPEN":
        actions.append("Start investigation - Mark as INVESTIGATING")

    if severity == "CRITICAL":
        actions.extend([
            "Block user account temporarily",
            "Escalate to fraud team lead",
            "Review all related sessions",
        ])
    elif severity == "HIGH":
        actions.extend([
            "Contact user for verification",
            "Review transaction history",
            "Check device fingerprint history",
        ])
    else:
        actions.extend([
            "Review evidence timeline",
            "Compare with similar cases",
            "Make resolution decision",
        ])

    return actions
