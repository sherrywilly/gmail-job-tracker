from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.ai import ClassifyRequest, ClassifyResponse
from app.services.ai_service import classify_text


router = APIRouter(prefix="/ai")


@router.post("/classify", response_model=ClassifyResponse)
async def classify(
    payload: ClassifyRequest,
    _user: User = Depends(get_current_user),
    _db: AsyncSession = Depends(get_db),
) -> ClassifyResponse:
    result = await classify_text(payload.email)
    return ClassifyResponse(result=result)
