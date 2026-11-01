from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from backend.models import Language

router = APIRouter(tags=["reports"])


@router.get("/cases/{case_id}/report", status_code=501, responses={501: {"description": "Owned by Stage 3"}})
async def get_report(case_id: UUID, lang: Language = Query(default=Language.MR)) -> None:
    """Render the verified Marathi or English report; implemented by Stage 3."""
    raise HTTPException(status_code=501, detail="owned by stage 3")
