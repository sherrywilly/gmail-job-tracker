from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.init_db import init_db


configure_logging()

app = FastAPI(title=settings.app_name)
app.include_router(api_router)

app_dir = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(app_dir / "static")), name="static")


@app.on_event("startup")
async def on_startup() -> None:
    if settings.auto_create_tables:
        await init_db()
