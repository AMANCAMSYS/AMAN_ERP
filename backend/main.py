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
from datetime import datetime, timezone
import logging

from config import settings
from database import engine

# ── Core & Auth ────────────────────────────────────────────────────────────────
from routers import auth, companies, roles, branches, settings as company_settings
from routers import audit, notifications, approvals, security, data_import

# ── Accounting & Finance ────────────────────────────────────────────────────────
from routers import accounting, currencies, cost_centers, budgets, reconciliation
from routers import treasury, taxes, costing_policies, checks, notes, assets

# ── Sales, Purchases & Inventory ───────────────────────────────────────────────
from routers import sales, purchases, inventory, parties

# ── HR & Manufacturing ──────────────────────────────────────────────────────────
from routers import hr, hr_advanced, manufacturing

# ── Projects, Expenses & Reports ───────────────────────────────────────────────
from routers import projects, expenses, reports, scheduled_reports, dashboard

# ── Commerce & External ────────────────────────────────────────────────────────
from routers import pos, contracts, crm, external

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
            
            # Create system_companies table for company registry
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS system_companies (
                    id VARCHAR(100) PRIMARY KEY,
                    company_name VARCHAR(255) NOT NULL,
                    company_name_en VARCHAR(255),
                    commercial_registry VARCHAR(100),
                    tax_number VARCHAR(100),
                    phone VARCHAR(50),
                    email VARCHAR(255),
                    address TEXT,
                    city VARCHAR(100),
                    country VARCHAR(100) DEFAULT 'SA',
                    logo_url TEXT,
                    database_name VARCHAR(255),
                    database_user VARCHAR(255),
                    currency VARCHAR(10) DEFAULT 'SAR',
                    timezone VARCHAR(50) DEFAULT 'Asia/Riyadh',
                    status VARCHAR(20) DEFAULT 'active',
                    plan_type VARCHAR(50) DEFAULT 'basic',
                    max_users INTEGER DEFAULT 10,
                    subscription_end DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    activated_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_system_companies_status 
                    ON system_companies(status);
            """))
            
            # Create system_activity_log table for global audit trail
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS system_activity_log (
                    id SERIAL PRIMARY KEY,
                    company_id VARCHAR(100),
                    action_type VARCHAR(100) NOT NULL,
                    action_description TEXT,
                    performed_by VARCHAR(255),
                    ip_address VARCHAR(50),
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_system_activity_log_action 
                    ON system_activity_log(action_type);
                CREATE INDEX IF NOT EXISTS idx_system_activity_log_date 
                    ON system_activity_log(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_system_activity_log_company 
                    ON system_activity_log(company_id);
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

# CORS — قائمة بيضاء دقيقة للـ origins
def _build_origins() -> list[str]:
    """Build allowed origins from settings — supports comma-separated ALLOWED_ORIGINS env var"""
    if settings.ALLOWED_ORIGINS:
        return [o.strip() for o in settings.ALLOWED_ORIGINS.split(',') if o.strip()]
    origins = [settings.FRONTEND_URL]
    if settings.FRONTEND_URL_PRODUCTION:
        origins.append(settings.FRONTEND_URL_PRODUCTION)
    return origins

origins = _build_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept", "Origin"],
    expose_headers=["Content-Disposition"],
    max_age=600,
)

# API-001: Rate Limiting — مشترك عبر shared limiter
from utils.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
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



# ── Core & Auth ─────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api")
app.include_router(companies.router, prefix="/api")
app.include_router(roles.router, prefix="/api")
app.include_router(branches.router, prefix="/api")
app.include_router(company_settings.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(approvals.router, prefix="/api")
app.include_router(security.router, prefix="/api")
app.include_router(data_import.router, prefix="/api")

# ── Accounting & Finance ─────────────────────────────────────────
app.include_router(accounting.router, prefix="/api")
app.include_router(currencies.router, prefix="/api")
app.include_router(cost_centers.router, prefix="/api")
app.include_router(budgets.router, prefix="/api")
app.include_router(reconciliation.router, prefix="/api")
app.include_router(treasury.router, prefix="/api")
app.include_router(taxes.router, prefix="/api")
app.include_router(costing_policies.router, prefix="/api")
app.include_router(checks.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(assets.router, prefix="/api")

# ── Sales, Purchases & Inventory ────────────────────────────────
app.include_router(sales.router, prefix="/api")
app.include_router(purchases.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(parties.router, prefix="/api")

# ── HR & Manufacturing ───────────────────────────────────────────
app.include_router(hr.router, prefix="/api")
app.include_router(hr_advanced.router, prefix="/api")
app.include_router(manufacturing.router, prefix="/api")

# ── Projects, Expenses & Reports ────────────────────────────────
app.include_router(projects.router, prefix="/api")
app.include_router(expenses.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(scheduled_reports.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")

# ── Commerce & External ──────────────────────────────────────────
app.include_router(pos.router, prefix="/api")
app.include_router(contracts.router, prefix="/api")
app.include_router(crm.router, prefix="/api")
app.include_router(external.router, prefix="/api")


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
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
