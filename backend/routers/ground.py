from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, HTTPException

router = APIRouter(tags=["ground evidence"])


@router.post("/cases/{case_id}/ground", status_code=501, responses={501: {"description": "Owned by Stage 2"}})
async def submit_ground(case_id: UUID, payload: dict[str, Any] = Body(...)) -> None:
    """Submit structured ground evidence; implemented by Stage 2."""
    raise HTTPException(status_code=501, detail="owned by stage 2")
