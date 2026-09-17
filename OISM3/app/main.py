from datetime import datetime
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import event, text
from app.config import settings
from app.database import engine, is_sqlite
from app.api.router import api_router

app = FastAPI(title="OISM API", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@app.get("/", include_in_schema=False)
def root():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "OISM API", "database": "ok"}
    except Exception as exc:
        return {"status": "degraded", "service": "OISM API", "database": "error", "error_type": type(exc).__name__}


if is_sqlite():
    @event.listens_for(engine, "connect")
    def _sqlite_functions(dbapi_connection, connection_record):
        dbapi_connection.create_function("NOW", 0, lambda: datetime.utcnow().isoformat(sep=" "))
        dbapi_connection.create_function("GREATEST", -1, lambda *args: max(args))


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
