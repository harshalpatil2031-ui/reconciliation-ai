from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, HTTPException

router = APIRouter(tags=["cases"])


def _unimplemented() -> None:
    raise HTTPException(status_code=501, detail="owned by stage 4")


@router.post("/cases", status_code=501, responses={501: {"description": "Owned by Stage 4"}})
async def create_case(payload: dict[str, Any] = Body(...)) -> None:
    """Create or update a case; implemented by Stage 4."""
    _unimplemented()


@router.get("/cases/{case_id}", status_code=501, responses={501: {"description": "Owned by Stage 4"}})
async def get_case(case_id: UUID) -> None:
    """Return case evidence and analysis; implemented by Stage 4."""
    _unimplemented()


@router.post("/cases/{case_id}/review", status_code=501, responses={501: {"description": "Owned by Stage 4"}})
async def review_case(case_id: UUID, payload: dict[str, Any] = Body(...)) -> None:
    """Record an officer review; implemented by Stage 4."""
    _unimplemented()
