from fastapi import APIRouter

from app.api.routes import ai, auth, dashboard, emails, health
from app.core.config import settings


api_router = APIRouter(prefix=settings.api_prefix)

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(emails.router, tags=["emails"])
api_router.include_router(ai.router, tags=["ai"])
api_router.include_router(dashboard.router, tags=["dashboard"])
