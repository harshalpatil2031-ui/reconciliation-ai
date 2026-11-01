from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["audit"])


@router.get("/audit/verify", status_code=501, responses={501: {"description": "Owned by Stage 3"}})
async def verify_audit_chain() -> None:
    """Verify the full audit hash chain; implemented by Stage 3."""
    raise HTTPException(status_code=501, detail="owned by stage 3")
