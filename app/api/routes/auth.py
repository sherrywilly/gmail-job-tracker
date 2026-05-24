from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.schemas.auth import RegisterRequest, TokenResponse
from app.services.user_service import create_user, get_user_by_email


router = APIRouter(prefix="/auth")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> None:
    existing = await get_user_by_email(db, email=payload.email)
    if existing is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    await create_user(db, email=payload.email, password_hash=get_password_hash(payload.password))


@router.post("/token", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await get_user_by_email(db, email=form.username)
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token, token_type="bearer")
