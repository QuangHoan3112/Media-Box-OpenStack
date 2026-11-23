from fastapi import FastAPI
from datetime import datetime, timezone

app = FastAPI(
    title="MediaBox API",
    description="MediaBox on OpenStack Private Cloud",
    version="1.0.0",
)

@app.get("/")
def home():
    return {
        "application": "MediaBox",
        "message": "MediaBox Backend is running",
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "mediabox-api",
    }

@app.get("/api/system/info")
def system_info():
    return {
        "application": "MediaBox",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "storage": "OpenStack Swift",
        "database": "PostgreSQL",
    }


# MediaBox authentication routes
from app.auth import router as auth_router
app.include_router(auth_router)


# Media management routes
from app.media import router as media_router
from app.upload import router as upload_router
app.include_router(upload_router)
app.include_router(media_router)


# Media permission routes
from app.permissions import router as permissions_router
app.include_router(permissions_router)


# Media playback and download
from app.playback import router as playback_router
app.include_router(playback_router)


# MediaBox web interface
from pathlib import Path
from fastapi.responses import FileResponse

@app.get("/app", include_in_schema=False)
def mediabox_frontend():
    return FileResponse(
        Path(__file__).resolve().parent / "static" / "index.html",
        headers={"Cache-Control": "no-store"},
    )
