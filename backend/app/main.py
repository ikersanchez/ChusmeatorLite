"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
import os
from app.config import settings
from app.database import init_db
from app.routers import pins, areas, general, votes, comments, admin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Chusmeator API",
    description="Backend API for Chusmeator interactive map application",
    version="1.0.0"
)

# Add Session Middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie=settings.session_cookie_name,
    max_age=3600 * 24 * 7,  # 1 week
    same_site="lax",
    https_only=False,  # Set to True in production with HTTPS
)

# Configure CORS - restrict to known origins
origins = settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Key"], # Only allow necessary headers
)

# Include routers
app.include_router(general.router)
app.include_router(pins.router)
app.include_router(areas.router)

app.include_router(votes.router)
app.include_router(comments.router)
app.include_router(admin.router)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    init_db()



@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/{catchall:path}")
async def serve_frontend(catchall: str):
    """Catch-all route to serve static files or index.html for SPA."""
    # Check if we should serve a static file from /static
    # (FastAPI mount handles /static prefix, but index.html etc might be at root)
    if catchall == "" or catchall == "index.html":
        return FileResponse(os.path.join(static_dir, "index.html"))
    
    file_path = os.path.join(static_dir, catchall)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Fallback to index.html for SPA routing
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # If no static dir, return a simple JSON response
    return {
        "message": "Chusmeator API",
        "status": "Frontend not found",
        "docs": "/docs"
    }
