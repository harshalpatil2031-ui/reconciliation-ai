from uuid import UUID

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["analysis"])


@router.post("/cases/{case_id}/analyze", status_code=501, responses={501: {"description": "Owned by Stage 3"}})
async def analyze_case(case_id: UUID) -> None:
    """Run the idempotent analysis pipeline; implemented by Stage 3."""
    raise HTTPException(status_code=501, detail="owned by stage 3")
