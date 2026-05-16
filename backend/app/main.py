"""FastAPI entrypoint."""
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from .config import settings
from .database import Base, engine
from . import models  # noqa: F401 — registers all model classes
from .routers import auth, users, employees, departments, salary, payroll, statutory, reports, compliance, dashboard

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s — %(message)s")
log = logging.getLogger("payroll")

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION,
              docs_url="/api/docs", redoc_url="/api/redoc",
              openapi_url="/api/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    log.info("Creating database tables if needed...")
    Base.metadata.create_all(bind=engine)

    # Seed if empty
    from .database import SessionLocal
    from .models.user import User
    from sqlalchemy import select, func
    db = SessionLocal()
    try:
        count = db.scalar(select(func.count(User.id))) or 0
        if count == 0:
            log.info("No users found — running initial seed...")
            from . import seed
            seed.run(db)
            db.commit()
            log.info("Seed complete. Default credentials: admin/Admin@1234, hr/Hr@1234")
    finally:
        db.close()


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "version": settings.APP_VERSION, "name": settings.APP_NAME}


# Routers
API = settings.API_PREFIX
app.include_router(auth.router, prefix=API)
app.include_router(users.router, prefix=API)
app.include_router(employees.router, prefix=API)
app.include_router(departments.router, prefix=API)
app.include_router(salary.router, prefix=API)
app.include_router(salary.tax_router, prefix=API)
app.include_router(payroll.router, prefix=API)
app.include_router(statutory.router, prefix=API)
app.include_router(reports.router, prefix=API)
app.include_router(compliance.router, prefix=API)
app.include_router(dashboard.router, prefix=API)


# Serve frontend static files (built by Vite)
import os
_env_dist = os.environ.get("FRONTEND_DIST")
if _env_dist:
    frontend_dist = Path(_env_dist)
else:
    frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(frontend_dist / "index.html")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        if full_path.startswith("api"):
            return JSONResponse({"detail": "Not found"}, status_code=404)
        candidate = frontend_dist / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    def root():
        return {"name": settings.APP_NAME, "version": settings.APP_VERSION,
                "docs": "/api/docs", "frontend": "not built"}
