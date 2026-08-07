import os
import asyncio
from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from dashboard.backend.core.sse import init_sse_state
from dashboard.backend.routers import stream, clips, analytics

app = FastAPI(
    title="ClipForge API",
    description="Backend API serving the single-operator content generation, review, publishing, and analytics dashboard.",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    init_sse_state(asyncio.get_running_loop())

# Enable CORS for React frontend (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated media short files
os.makedirs("generator/output", exist_ok=True)
app.mount("/api/media", StaticFiles(directory="generator/output"), name="media")

@app.get("/")
def health_check():
    """API Root Health Check endpoint."""
    return {
        "status": "ok",
        "message": "ClipForge API is up and running",
        "timestamp": datetime.utcnow().isoformat()
    }

app.include_router(stream.router, prefix="/api", tags=["stream"])
app.include_router(clips.router, prefix="/api", tags=["clips"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])

