from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.email import EmailClassificationResponse, EmailListResponse, EmailResponse
from app.services.classification_service import classify_and_store_email
from app.services.email_service import get_email_for_user, list_emails_for_user
from app.workers.tasks import enqueue_sync_inbox


router = APIRouter(prefix="/emails")


@router.get("/", response_model=EmailListResponse)
async def list_emails(
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EmailListResponse:
    emails = await list_emails_for_user(db, user_id=user.id, unread_only=unread_only, limit=limit, offset=offset)
    return EmailListResponse(emails=emails)


@router.get("/{email_id}", response_model=EmailResponse)
async def get_email(
    email_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EmailResponse:
    email = await get_email_for_user(db, user_id=user.id, email_id=email_id)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    return EmailResponse.model_validate(email)


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_now(user: User = Depends(get_current_user)) -> None:
    enqueue_sync_inbox(user_id=user.id)


@router.post("/{email_id}/classify", response_model=EmailClassificationResponse)
async def classify_email(
    email_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EmailClassificationResponse:
    email = await get_email_for_user(db, user_id=user.id, email_id=email_id)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    classification = await classify_and_store_email(db, email=email)
    return EmailClassificationResponse.model_validate(classification)
