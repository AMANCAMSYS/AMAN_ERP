"""
AMAN ERP - Main Application
نظام أمان لإدارة الموارد المؤسسية
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException
import os
from contextlib import asynccontextmanager
from sqlalchemy import text
from datetime import datetime
import logging

from config import settings
from database import engine
from routers import auth, companies, accounting, sales, inventory, purchases, reports, audit, roles, currencies, settings as company_settings, parties, projects, expenses

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """إدارة دورة حياة التطبيق"""
    logger.info("🚀 Starting AMAN ERP System...")
    
    # SEC-004: Warn if SECRET_KEY is weak/default
    if len(settings.SECRET_KEY) < 32 or settings.SECRET_KEY.startswith("your-"):
        logger.critical("🔴 SECURITY WARNING: SECRET_KEY is weak or default! Change it in .env immediately!")
        logger.critical("   Generate a strong key: python3 -c \"import secrets; print(secrets.token_hex(32))\"")
    
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            # DB-015: Create central user index table for O(1) login lookup
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS system_user_index (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) NOT NULL,
                    company_id VARCHAR(100) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(username, company_id)
                );
                CREATE INDEX IF NOT EXISTS idx_system_user_index_username 
                    ON system_user_index(username);
            """))
            conn.commit()
        logger.info("✅ Database connected")
        
        # Start Background Stats Worker
        from routers.dashboard import update_system_stats_task
        import asyncio
        asyncio.create_task(update_system_stats_task())
        logger.info("📡 System Stats Background Worker Started")
        
        # SEC-201: Start token blacklist cleanup task
        async def _blacklist_cleanup_loop():
            from routers.auth import cleanup_expired_blacklist
            while True:
                try:
                    cleanup_expired_blacklist()
                except Exception:
                    pass
                await asyncio.sleep(3600)  # Every hour
        asyncio.create_task(_blacklist_cleanup_loop())
        logger.info("🧹 Token Blacklist Cleanup Worker Started")
        
        # Start Report Scheduler
        from services.scheduler import start_scheduler
        start_scheduler()
        logger.info("⏰ Report Scheduler Started")
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
    
    yield
    
    logger.info("⏹️ Stopping AMAN ERP System...")
    engine.dispose()


app = FastAPI(
    title="AMAN ERP System",
    description="نظام أمان لإدارة الموارد المؤسسية - 91 جدول متكامل ",
    version="1.0.0",
    # Trigger reload
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
origins = [settings.FRONTEND_URL]
if settings.FRONTEND_URL_PRODUCTION:
    origins.append(settings.FRONTEND_URL_PRODUCTION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# API-001: Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# SEC-203: HTTPS Enforcement + Security Headers
# SEC-204: Input Sanitization (XSS/SQLi detection)
from utils.security_middleware import HTTPSRedirectMiddleware, InputSanitizationMiddleware
app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(InputSanitizationMiddleware)

# Static Files (Logos, attachments)
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(os.path.join(uploads_dir, "logos"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


# Global exception handler: sanitize 500 error messages to prevent info leakage
@app.exception_handler(FastAPIHTTPException)
async def sanitize_http_exception(request: Request, exc: FastAPIHTTPException):
    if exc.status_code == 500:
        # Log the real error for debugging
        logger.error(f"Internal error on {request.method} {request.url.path}: {exc.detail}")
        # Return generic message to client (hide SQL/internal details)
        return JSONResponse(
            status_code=500,
            content={"detail": "حدث خطأ داخلي في الخادم. يرجى المحاولة لاحقاً أو الاتصال بالدعم الفني."}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# Global unhandled exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "حدث خطأ داخلي في الخادم. يرجى المحاولة لاحقاً أو الاتصال بالدعم الفني."}
    )


app.include_router(auth.router, prefix="/api")
app.include_router(companies.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(sales.router, prefix="/api")
app.include_router(accounting.router, prefix="/api")
app.include_router(purchases.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(roles.router, prefix="/api")

from routers import cost_centers
app.include_router(cost_centers.router, prefix="/api")

from routers import hr
app.include_router(hr.router, prefix="/api")

from routers import hr_advanced
from routers import manufacturing
app.include_router(hr_advanced.router, prefix="/api")
app.include_router(manufacturing.router, prefix="/api")

from routers import treasury
app.include_router(treasury.router, prefix="/api")

from routers import branches
app.include_router(branches.router)

from routers import budgets
app.include_router(budgets.router, prefix="/api")

from routers import reconciliation
app.include_router(reconciliation.router, prefix="/api")

from routers import pos
app.include_router(pos.router, prefix="/api")

from routers import assets
app.include_router(assets.router, prefix="/api")

from routers import dashboard
app.include_router(dashboard.router, prefix="/api")

app.include_router(company_settings.router, prefix="/api")
app.include_router(parties.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(expenses.router, prefix="/api")
app.include_router(currencies.router, prefix="/api")

from routers import contracts, taxes, costing_policies

app.include_router(contracts.router, prefix="/api")
app.include_router(taxes.router, prefix="/api")
app.include_router(costing_policies.router)

from routers import checks
app.include_router(checks.router, prefix="/api")

from routers import notes
from routers import scheduled_reports

app.include_router(notes.router, prefix="/api")
app.include_router(scheduled_reports.router, prefix="/api")

from routers import notifications
app.include_router(notifications.router, prefix="/api")

from routers import approvals
app.include_router(approvals.router, prefix="/api")

from routers import security
app.include_router(security.router, prefix="/api")

from routers import data_import
app.include_router(data_import.router, prefix="/api")

from routers import external, crm
app.include_router(external.router, prefix="/api")
app.include_router(crm.router, prefix="/api")

from routers import external, crm
app.include_router(external.router, prefix="/api")
app.include_router(crm.router, prefix="/api")


@app.get("/")
def root():
    return {
        "system": "AMAN ERP",
        "version": "1.0.0",
        "status": "running",
        "features": {
            "auto_company_id": True,
            "multi_tenant": True,
            "total_tables": 91
        },
        "docs": "/api/docs"
    }


@app.get("/health")
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
