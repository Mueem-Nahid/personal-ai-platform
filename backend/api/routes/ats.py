from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_session
from schemas.ats import AtsRefineRequest, AtsReport
from services.ats_service import AtsService, StaleAtsReportError
from workers.redis_pool import get_redis

router = APIRouter()
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/{version_id}/ats", response_model=AtsReport | None)
async def get_ats(version_id: UUID, session: SessionDep) -> AtsReport | None:
    try:
        return await AtsService(session).get_report(version_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{version_id}/ats", response_model=AtsReport)
async def evaluate_ats(version_id: UUID, session: SessionDep) -> AtsReport:
    try:
        return await AtsService(session).evaluate(version_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{version_id}/refine", status_code=status.HTTP_202_ACCEPTED)
async def refine_ats(
    version_id: UUID, body: AtsRefineRequest, session: SessionDep
) -> dict[str, str | int]:
    try:
        redis = await get_redis()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="The refinement queue is unavailable") from exc
    try:
        version = await AtsService(session).create_refinement(version_id, body.fingerprint)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except StaleAtsReportError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        await redis.enqueue_job("optimize_resume", str(version.id))
    except Exception as exc:
        version.status = "failed"
        version.error = (
            "Could not enqueue ATS refinement. Retry when the worker queue is available."
        )
        await session.commit()
        raise HTTPException(status_code=503, detail=version.error) from exc
    return {
        "resume_version_id": str(version.id),
        "version_no": version.version_no,
        "status": version.status,
    }
