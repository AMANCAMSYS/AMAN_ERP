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

# ── Observability ──────────────────────────────────────────────────────────────
_SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
if _SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        sentry_sdk.init(
            dsn=_SENTRY_DSN,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            environment=os.environ.get("APP_ENV", "production"),
            release=f"aman-erp@2.0.0",
        )
        logging.getLogger(__name__).info("✅ Sentry initialized")
    except ImportError:
        pass  # sentry-sdk not installed — skip silently

# ── Core & Auth ────────────────────────────────────────────────────────────────
from routers import auth, companies, roles, branches, settings as company_settings
from routers import audit, notifications, approvals, security, data_import

# ── Accounting & Finance (routers/finance/) ─────────────────────────────────────
from routers import finance

# ── Sales, Purchases & Inventory ───────────────────────────────────────────────
from routers import sales, purchases, inventory, parties

# ── HR (routers/hr/) & Manufacturing (routers/manufacturing/) ───────────────────
from routers import hr, manufacturing

# ── Projects & Reports ─────────────────────────────────────────────────────────
from routers import projects, reports, scheduled_reports, dashboard

# ── Commerce & External ────────────────────────────────────────────────────────
from routers import pos, contracts, crm, external, services

# ── Role-Based KPI Dashboards ──────────────────────────────────────────────────
from routers import role_dashboards

# ── System Completion (Phase 100%) ─────────────────────────────────────────────
from routers import delivery_orders, landed_costs, hr_wps_compliance
from routers import system_completion
from routers import sso, matching, mobile

# OPS-001: Structured logging — JSON in production, human-readable in dev
from utils.logging_config import setup_logging, RequestIDMiddleware
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """إدارة دورة حياة التطبيق"""
    logger.info("🚀 Starting AMAN ERP System...")
    
    # SEC-004: Warn if SECRET_KEY is weak/default
    if len(settings.SECRET_KEY) < 32 or settings.SECRET_KEY.startswith("your-"):
        logger.critical("🔴 SECURITY WARNING: SECRET_KEY is weak or default! Change it in .env immediately!")
        logger.critical("   Generate a strong key: python3 -c \"import secrets; print(secrets.token_hex(32))\"")
    
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
                logo_url VARCHAR(255),
                database_name VARCHAR(255),
                database_user VARCHAR(255),
                currency VARCHAR(10) DEFAULT 'SAR',
                timezone VARCHAR(50) DEFAULT 'Asia/Riyadh',
                status VARCHAR(20) DEFAULT 'active',
                plan_type VARCHAR(50) DEFAULT 'basic',
                max_users INTEGER DEFAULT 10,
                subscription_end DATE,
                template_id INTEGER,
                enabled_modules JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                activated_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_system_companies_status
                ON system_companies(status);
        """))

        # Industry Templates Table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS industry_templates (
                id SERIAL PRIMARY KEY,
                key VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                name_ar VARCHAR(100) NOT NULL,
                description TEXT,
                description_ar TEXT,
                icon VARCHAR(10),
                enabled_modules JSONB NOT NULL,
                default_settings JSONB
            );

        """))
        
        # Seed Industry Templates (12 types)
        conn.execute(text("""
            INSERT INTO industry_templates (key, name, name_ar, description, description_ar, icon, enabled_modules)
            VALUES 
            ('retail', 'Retail', 'تجارة التجزئة', 'Grocery, clothing, electronics, gifts', 'بقالات، ملابس، إلكترونيات، عطور، هدايا', '🛍️', '["dashboard","kpi","accounting","assets","treasury","sales","pos","buying","stock","crm","expenses","taxes","approvals","reports","hr","audit","roles","settings","data_import","sso","analytics","performance","cashflow","campaigns","subscriptions","matching","forecast"]'),
            ('wholesale', 'Wholesale & Distribution', 'الجملة والتوزيع', 'Distributors, wholesale warehouses, agents, importers', 'موزعين، مستودعات جملة، وكلاء بيع، مستوردين', '📦', '["dashboard","kpi","accounting","assets","treasury","sales","buying","stock","crm","expenses","taxes","approvals","reports","hr","audit","roles","settings","data_import","sso","analytics","performance","cashflow","campaigns","matching","intercompany","forecast"]'),
            ('restaurant', 'Food & Beverage', 'المطاعم والمقاهي', 'Restaurants, cafes, cloud kitchens, food trucks, bakeries', 'مطاعم، كافيهات، مطابخ سحابية، فود ترك، مخابز', '🍽️', '["dashboard","kpi","accounting","assets","treasury","sales","pos","buying","stock","crm","expenses","taxes","approvals","reports","hr","audit","roles","settings","data_import","sso","analytics","performance","cashflow","subscriptions","forecast"]'),
            ('manufacturing', 'Manufacturing', 'التصنيع والإنتاج', 'Factories, production workshops, packaging', 'مصانع، ورش إنتاج، تعبئة وتغليف', '🏭', '["dashboard","kpi","accounting","assets","treasury","sales","buying","stock","manufacturing","projects","crm","services","expenses","taxes","approvals","reports","hr","audit","roles","settings","data_import","sso","analytics","performance","cashflow","campaigns","matching","intercompany","forecast","shop_floor","cpq","subscriptions"]'),
            ('construction', 'Construction', 'المقاولات والمشاريع', 'General contracting, finishing, plumbing, electrical', 'مقاولات عامة، تشطيب، سباكة، كهرباء، طرق', '🏗️', '["dashboard","kpi","accounting","assets","treasury","sales","buying","stock","projects","crm","services","expenses","taxes","approvals","reports","hr","audit","roles","settings","data_import","sso","analytics","performance","cashflow","campaigns","matching","intercompany"]'),
            ('services', 'Professional Services', 'الخدمات المهنية', 'Accounting, law, consulting, training, marketing', 'محاسبة، محاماة، استشارات، تدريب، تسويق', '💼', '["dashboard","kpi","accounting","assets","treasury","sales","buying","projects","crm","services","expenses","taxes","approvals","reports","hr","audit","roles","settings","data_import","sso","analytics","performance","cashflow","campaigns","subscriptions","intercompany","cpq"]'),
            ('pharmacy', 'Pharmacy & Medical', 'الصيدليات والمستلزمات الطبية', 'Pharmacies, medical supplies, labs, small clinics', 'صيدليات، مستلزمات طبية، مختبرات، عيادات', '💊', '["dashboard","kpi","accounting","assets","treasury","sales","pos","buying","stock","crm","expenses","taxes","approvals","reports","hr","audit","roles","settings","data_import","sso","analytics","performance","cashflow","matching","forecast","subscriptions"]'),
            ('workshop', 'Workshops & Repair', 'الورش والصيانة', 'Auto mechanics, electrical repair, device repair', 'ميكانيك، كهرباء سيارات، صيانة أجهزة', '🔧', '["dashboard","kpi","accounting","assets","treasury","sales","pos","buying","stock","crm","services","expenses","taxes","approvals","reports","hr","audit","roles","settings","data_import","sso","analytics","performance","cashflow"]'),
            ('ecommerce', 'E-Commerce', 'التجارة الإلكترونية', 'Online stores, social media selling, marketplaces', 'متاجر أونلاين، بيع عبر منصات التواصل', '🛒', '["dashboard","kpi","accounting","assets","treasury","sales","buying","stock","crm","expenses","taxes","approvals","reports","hr","audit","roles","settings","data_import","sso","analytics","performance","cashflow","campaigns","subscriptions","cpq","forecast"]'),
            ('logistics', 'Logistics & Transport', 'النقل والخدمات اللوجستية', 'Freight, delivery, warehousing, cargo transport', 'شحن، توصيل، مستودعات، نقل بضائع', '🚛', '["dashboard","kpi","accounting","assets","treasury","sales","buying","stock","crm","services","expenses","taxes","approvals","reports","hr","audit","roles","settings","data_import","sso","analytics","performance","cashflow","matching","intercompany","forecast"]'),
            ('agriculture', 'Agriculture', 'الزراعة والتجارة الزراعية', 'Farms, crop traders, feed, poultry', 'مزارع، تجار محاصيل، أعلاف، دواجن', '🌾', '["dashboard","kpi","accounting","assets","treasury","sales","buying","stock","crm","expenses","taxes","approvals","reports","hr","audit","roles","settings","data_import","sso","analytics","performance","cashflow","forecast"]'),
            ('general', 'Multi-Activity', 'نشاط عام', 'Comprehensive system with all modules', 'نظام شامل لجميع الأنشطة', '🌐', '["dashboard","kpi","accounting","assets","treasury","sales","pos","buying","stock","manufacturing","projects","crm","services","expenses","taxes","approvals","reports","hr","audit","roles","settings","data_import","sso","analytics","performance","cashflow","campaigns","matching","intercompany","subscriptions","cpq","forecast","shop_floor"]')
            ON CONFLICT (key) DO UPDATE SET 
                name = EXCLUDED.name,
                name_ar = EXCLUDED.name_ar,
                description = EXCLUDED.description,
                description_ar = EXCLUDED.description_ar,
                icon = EXCLUDED.icon,
                enabled_modules = EXCLUDED.enabled_modules;
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
    # TASK-028: web process only starts the in-process scheduler when mode is
    # `in_process`. For production multi-replica deployments, set
    # SCHEDULER_MODE=dedicated and run backend/worker.py as a separate service
    # so jobs fire exactly once regardless of web replica count.
    scheduler_mode = (getattr(settings, "SCHEDULER_MODE", "in_process") or "in_process").lower()
    if scheduler_mode == "in_process":
        from services.scheduler import start_scheduler
        start_scheduler()
        logger.info("⏰ Report Scheduler Started (in-process)")
    else:
        logger.info("⏰ Report Scheduler NOT started in web process (SCHEDULER_MODE=%s)", scheduler_mode)

    # TASK-041: discover and register plugins (drop packages into backend/plugins/).
    try:
        from utils.plugin_registry import load_plugins
        loaded = load_plugins(app)
        if loaded:
            logger.info("🔌 Plugins registered: %s", ", ".join(loaded))
    except Exception:
        logger.exception("Plugin loading failed (non-fatal)")

    # Phase 6: optional Redis Streams bridge for the domain event bus.
    # Enabled by setting REDIS_EVENT_BUS=1 in the environment.
    try:
        from utils.redis_event_bus import install as _install_redis_bus, is_enabled as _bus_enabled
        if _bus_enabled():
            if _install_redis_bus():
                logger.info("📡 Redis event-bus bridge installed")
    except Exception:
        logger.exception("Redis event bus install failed (non-fatal)")
    
    # Sync schema for all existing company databases via Alembic migrations
    try:
        import subprocess, sys as _sys
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        alembic_ini = os.path.join(backend_dir, "alembic.ini")
        alembic_cmd = [
            _sys.executable, "-m", "alembic",
            "-c", alembic_ini,
            "-x", "company=all",
            "upgrade", "head",
        ]
        result = subprocess.run(
            alembic_cmd, cwd=backend_dir,
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0:
            logger.info("🔄 Alembic migrations applied for all company databases")
        else:
            logger.warning(f"⚠️ Alembic migration warnings: {result.stderr or result.stdout}")
    except Exception as e:
        logger.warning(f"⚠️ Schema sync skipped: {e}")
    
    yield
    
    logger.info("⏹️ Stopping AMAN ERP System...")
    engine.dispose()


app = FastAPI(
    title="AMAN ERP System",
    description="""
# نظام أمان لإدارة الموارد المؤسسية (AMAN ERP)

نظام ERP متكامل متعدد الشركات (Multi-Tenant) مبني بـ **FastAPI** و **PostgreSQL**.

## الوحدات الرئيسية

| الوحدة | الوصف |
|--------|-------|
| 📊 المحاسبة | دليل حسابات، قيود يومية، ميزان مراجعة، قوائم مالية |
| 💰 المبيعات | فواتير، أوامر بيع، عروض أسعار، مرتجعات |
| 🛒 المشتريات | أوامر شراء، موردين، RFQ، اتفاقيات |
| 📦 المخزون | منتجات، مستودعات، تحويلات، تتبع دفعات وأرقام تسلسلية |
| 🏦 الخزينة | حسابات بنكية، تسويات، شيكات، سندات |
| 👥 الموارد البشرية | موظفين، رواتب، حضور، إجازات، تقييم أداء |
| 🏭 التصنيع | قوائم مواد (BOM)، أوامر إنتاج، مراكز عمل |
| 🏪 نقاط البيع | واجهة POS، عروض، برامج ولاء |
| 📐 المشاريع | إدارة مشاريع، مهام، موارد، Gantt |
| 📈 التقارير | تقارير مالية وتشغيلية، تقارير مجدولة |

## المصادقة

يستخدم النظام **JWT Bearer Token** — أرسل التوكن في header:
```
Authorization: Bearer <token>
```
""",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_tags=[
        # ── Core & Auth ──
        {"name": "المصادقة", "description": "تسجيل الدخول، JWT tokens، المصادقة الثنائية (2FA)، إدارة الجلسات"},
        {"name": "إدارة الشركات", "description": "إنشاء وإدارة الشركات (Multi-Tenant)، تهيئة قاعدة البيانات لكل شركة"},
        {"name": "إدارة الأدوار", "description": "أدوار المستخدمين والصلاحيات التفصيلية (RBAC)"},
        {"name": "branches", "description": "إدارة فروع الشركة وربط المستخدمين بالفروع"},
        {"name": "إعدادات الشركة", "description": "إعدادات عامة للشركة: عملة افتراضية، سنة مالية، شعار، إلخ"},
        {"name": "سجلات المراقبة", "description": "سجل المراجعة (Audit Log) — تتبع جميع العمليات والتعديلات"},
        {"name": "الإشعارات", "description": "إشعارات فورية عبر WebSocket وHTTP — إنشاء، قراءة، حذف"},
        {"name": "الاعتمادات", "description": "نظام الموافقات متعدد المستويات — سير عمل قابل للتخصيص"},
        {"name": "الأمان", "description": "إدارة مفاتيح API، Webhooks، سجل الأحداث الأمنية"},
        {"name": "استيراد/تصدير البيانات", "description": "استيراد بيانات من Excel/CSV — حسابات، منتجات، عملاء، موظفين"},

        # ── Accounting & Finance ──
        {"name": "المحاسبة", "description": "دليل الحسابات، القيود اليومية، الأرصدة الافتتاحية، قيود الإقفال، القيود المتكررة"},
        {"name": "accounting", "description": "العملات وأسعار الصرف — تحديث يومي وسجل تاريخي"},
        {"name": "مراكز التكلفة", "description": "إنشاء وإدارة مراكز التكلفة وتوزيع المصاريف"},
        {"name": "Budgets", "description": "إعداد الميزانيات التقديرية ومقارنتها بالفعلي — تنبيهات التجاوز"},
        {"name": "تسوية البنك", "description": "التسوية البنكية — استيراد كشف حساب، مطابقة تلقائية، تأكيد"},
        {"name": "الخزينة والمصروفات", "description": "حسابات بنكية ونقدية، مصروفات، تحويلات بين الحسابات، تقرير تدفقات نقدية"},
        {"name": "الضرائب", "description": "إعداد معدلات الضريبة، الإقرارات الضريبية، ضريبة الاستقطاع (WHT)"},
        {"name": "Costing Policies", "description": "سياسات تكلفة المخزون — FIFO, LIFO, متوسط مرجح، تكلفة معيارية"},
        {"name": "checks", "description": "شيكات القبض والدفع — إصدار، تحصيل، رفض، تحويل"},
        {"name": "أوراق القبض والدفع", "description": "سندات القبض والصرف — إنشاء، تأكيد، طباعة"},
        {"name": "الأصول الثابتة", "description": "إدارة الأصول — إهلاك، إعادة تقييم، صيانة، تأمين"},
        {"name": "المصاريف", "description": "مطالبات المصروفات — تقديم، موافقة، صرف، تقارير"},

        # ── Sales & Purchases ──
        {"name": "المبيعات", "description": "فواتير المبيعات، أوامر البيع، عروض الأسعار، المرتجعات، إيصالات القبض، إشعارات دائنة/مدينة"},
        {"name": "المشتريات", "description": "أوامر الشراء، فواتير المشتريات، المرتجعات، طلبات عروض أسعار (RFQ)، تقييم الموردين"},
        {"name": "المخزون", "description": "المنتجات، المستودعات، التحويلات، التسويات، حركات المخزون، الشحنات"},
        {"name": "Advanced Inventory Phase 2", "description": "تتبع الدفعات والأرقام التسلسلية، فحص الجودة، الجرد الدوري"},
        {"name": "الجهات (العملاء والموردين)", "description": "إدارة موحدة للعملاء والموردين — بيانات، كشوف حساب، أرصدة"},

        # ── HR ──
        {"name": "HR & Employees", "description": "الموظفين، الأقسام، المناصب، الرواتب، الحضور، الإجازات، القروض"},
        {"name": "HR Advanced - الموارد البشرية المتقدمة", "description": "تقييم الأداء، التدريب، المخالفات، العهد، التوظيف، العمل الإضافي"},

        # ── Manufacturing ──
        {"name": "Manufacturing (Phase 5)", "description": "مراكز العمل، خطوط الإنتاج، قوائم المواد (BOM)، أوامر الإنتاج، بطاقات العمل، MRP"},

        # ── Projects & Reports ──
        {"name": "المشاريع", "description": "إدارة المشاريع — مهام، موارد، ميزانيات، Gantt chart، تقارير تقدم"},
        {"name": "التقارير", "description": "ميزان المراجعة، قائمة الدخل، الميزانية العمومية، كشف حساب، تقارير المبيعات والمشتريات"},
        {"name": "Scheduled Reports", "description": "تقارير مجدولة — إعداد تقارير تلقائية تُرسل بالبريد الإلكتروني"},
        {"name": "لوحة التحكم", "description": "لوحة قيادة شاملة — إحصائيات مالية، رسوم بيانية، مؤشرات أداء"},

        # ── Commerce & External ──
        {"name": "Point of Sale", "description": "نقطة البيع — واجهة بيع، جلسات، عروض ترويجية، برامج ولاء، طاولات مطعم"},
        {"name": "Contracts", "description": "إدارة العقود — إنشاء، تجديد، إنهاء، تنبيهات الانتهاء"},
        {"name": "إدارة العلاقات CRM", "description": "فرص البيع (Pipeline)، تذاكر الدعم الفني، إدارة العملاء المحتملين"},
        {"name": "التكامل الخارجي", "description": "مفاتيح API، Webhooks، تكامل مع أنظمة خارجية"},
    ]
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

# OPS-001: Request-ID middleware — adds X-Request-ID to every request/response
app.add_middleware(RequestIDMiddleware)

# SEC-203: HTTPS Enforcement + Security Headers
# SEC-204: Input Sanitization (XSS/SQLi detection)
from utils.security_middleware import HTTPSRedirectMiddleware, InputSanitizationMiddleware
# FORCE_HTTPS must be explicitly enabled (e.g. after SSL cert is installed).
# When running on plain HTTP (IP-only, no domain/cert) keep it off to prevent
# the 301→HTTPS loop that causes ERR_CONNECTION_REFUSED in the browser.
if os.getenv("FORCE_HTTPS", "false").lower() == "true":
    app.add_middleware(HTTPSRedirectMiddleware)
else:
    # Still register the middleware for security headers only (no redirect)
    from utils.security_middleware import SecurityHeadersOnlyMiddleware
    app.add_middleware(SecurityHeadersOnlyMiddleware)
app.add_middleware(InputSanitizationMiddleware)

# SEC / TASK-030: CSRF double-submit-cookie protection. Enforcement mode is
# controlled via settings.CSRF_ENFORCEMENT (off | permissive | strict).
from utils.csrf_middleware import CSRFMiddleware
app.add_middleware(CSRFMiddleware)

# ── Prometheus Metrics ─────────────────────────────────────────────────────────
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/health", "/metrics", "/api/health"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    logger.info("✅ Prometheus metrics exposed at /metrics")
except ImportError:
    logger.warning("⚠️ prometheus-fastapi-instrumentator not installed — metrics disabled")

# Static Files (Logos, attachments)
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
try:
    os.makedirs(os.path.join(uploads_dir, "logos"), exist_ok=True)
except PermissionError as e:
    logger.warning(f"⚠️  Cannot create uploads/logos: {e} — entrypoint should handle this")
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
# Also mount under /api/uploads for consistency with API-prefixed calls in some components
app.mount("/api/uploads", StaticFiles(directory=uploads_dir), name="api_uploads")



# Global exception handler: sanitize 500 error messages to prevent info leakage
@app.exception_handler(FastAPIHTTPException)
async def sanitize_http_exception(request: Request, exc: FastAPIHTTPException):
    if exc.status_code == 500:
        # Log the real error for debugging
        logger.error(f"Internal error on {request.method} {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=500,
            content={"detail": "حدث خطأ داخلي في الخادم. يرجى المحاولة لاحقاً."}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# Global unhandled exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    import traceback
    tb = traceback.format_exc()
    logger.error(tb)
    return JSONResponse(
        status_code=500,
        content={"detail": "حدث خطأ داخلي في الخادم. يرجى المحاولة لاحقاً."}
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

# ── Accounting & Finance (12 sub-routers from routers/finance/) ──
app.include_router(finance.router, prefix="/api")

# ── Sales, Purchases & Inventory ────────────────────────────────
app.include_router(sales.router, prefix="/api")
app.include_router(purchases.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(parties.router, prefix="/api")

# ── HR (2 sub-routers) & Manufacturing ────────────────────────────
app.include_router(hr.router, prefix="/api")
app.include_router(manufacturing.router, prefix="/api")

# ── Projects & Reports ───────────────────────────────────────────
app.include_router(projects.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(scheduled_reports.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")

# ── Commerce & External ──────────────────────────────────────────
app.include_router(pos.router, prefix="/api")
app.include_router(contracts.router, prefix="/api")
app.include_router(crm.router, prefix="/api")
app.include_router(external.router, prefix="/api")
app.include_router(services.router, prefix="/api")
# ── Role-Based KPI Dashboards ────────────────────────────────────────────
app.include_router(role_dashboards.router, prefix="/api")
# ── System Completion (New modules) ──────────────────────────────
app.include_router(delivery_orders.router, prefix="/api")
app.include_router(landed_costs.router, prefix="/api")
app.include_router(hr_wps_compliance.router, prefix="/api")
app.include_router(system_completion.router, prefix="/api")
app.include_router(sso.router, prefix="/api")
app.include_router(matching.router, prefix="/api")
app.include_router(mobile.router, prefix="/api")


@app.get("/")
def root():
    return {
        "system": "AMAN ERP",
        "version": "2.0.0",
        "status": "running",
        "features": {
            "auto_company_id": True,
            "multi_tenant": True,
            "total_tables": 178
        },
        "docs": "/api/docs"
    }


@app.get("/api/health", tags=["Health"], summary="Health Check", include_in_schema=True)
def health_check():
    """
    فحص صحة النظام — يتحقق من:
    - اتصال قاعدة البيانات الرئيسية
    - عدد الشركات المسجلة
    - اتصال Redis (اختياري)
    - وقت الاستجابة
    """
    import time
    start = time.monotonic()
    
    checks: dict = {}
    overall = "healthy"

    # ── Database check ──
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM system_companies"))
            company_count = result.scalar()
        checks["database"] = {"status": "ok", "companies": company_count}
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)[:120]}
        overall = "degraded"

    # ── Redis check (optional) ──
    try:
        if settings.REDIS_URL:
            import redis as redis_lib
            r = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=2)
            r.ping()
            checks["redis"] = {"status": "ok"}
        else:
            checks["redis"] = {"status": "not_configured"}
    except Exception as e:
        checks["redis"] = {"status": "error", "detail": str(e)[:80]}
        # Redis is optional — don't degrade overall health

    elapsed_ms = round((time.monotonic() - start) * 1000, 2)

    return {
        "status": overall,
        "version": "2.0.0",
        "environment": os.environ.get("APP_ENV", "development"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "response_time_ms": elapsed_ms,
        "checks": checks,
    }


@app.get("/health", include_in_schema=False)
def health_check_root():
    """Alias for /api/health — used by Docker/load balancer health probes"""
    return health_check()
