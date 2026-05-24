from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.email_service import list_urgent_emails


router = APIRouter(prefix="/dashboard")
app_dir = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(app_dir / "templates"))


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    urgent = await list_urgent_emails(db, user_id=user.id, limit=25)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "user": user, "urgent_emails": urgent},
    )
