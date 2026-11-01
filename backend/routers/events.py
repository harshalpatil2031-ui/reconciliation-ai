from uuid import UUID

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["events"])


@router.get("/events/{event_id}/queue", status_code=501, responses={501: {"description": "Owned by Stage 4"}})
async def get_review_queue(event_id: str) -> None:
    """Return the officer review queue; implemented by Stage 4."""
    raise HTTPException(status_code=501, detail="owned by stage 4")


@router.get("/events/{event_id}/fairness", status_code=501, responses={501: {"description": "Owned by Stage 4"}})
async def get_fairness_summary(event_id: str) -> None:
    """Return disaggregated fairness measures; implemented by Stage 4."""
    raise HTTPException(status_code=501, detail="owned by stage 4")
