from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.init_db import init_db


configure_logging()

app = FastAPI(title=settings.app_name)
app.include_router(api_router)

app_dir = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(app_dir / "static")), name="static")

dashboard_dir = app_dir / "static" / "dashboard"
dashboard_index = dashboard_dir / "index.html"


@app.get("/dashboard", include_in_schema=False)
@app.get("/dashboard/{path:path}", include_in_schema=False)
async def react_dashboard(path: str = "") -> Response:
    if not dashboard_index.exists():
        return HTMLResponse(
            """
            <html>
              <head><title>Dashboard not built</title></head>
              <body style="font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:720px;margin:40px auto;padding:0 16px;">
                <h1>React dashboard not built</h1>
                <p>Build it from <code>frontend/</code>:</p>
                <pre><code>cd frontend
            npm install
            npm run build</code></pre>
                <p>Then refresh this page.</p>
                <p>You can still use the server-rendered dashboard at <a href="/api/dashboard/">/api/dashboard/</a>.</p>
              </body>
            </html>
            """,
        )

    if path:
        requested = Path(path)
        if requested.is_absolute() or ".." in requested.parts:
            return HTMLResponse(status_code=404, content="Not found")
        candidate = (dashboard_dir / requested).resolve()
        if dashboard_dir.resolve() in candidate.parents and candidate.is_file():
            return FileResponse(candidate)

    return FileResponse(dashboard_index)


@app.on_event("startup")
async def on_startup() -> None:
    if settings.auto_create_tables:
        await init_db()
