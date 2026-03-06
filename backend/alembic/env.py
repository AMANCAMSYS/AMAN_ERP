"""
AMAN ERP — Alembic environment configuration.

Supports multi-tenant: runs migrations on ALL company databases
when --x company=all is passed, or on a single company with --x company=<id>.

Usage:
    alembic upgrade head                          # system DB only
    alembic -x company=all upgrade head           # all company DBs
    alembic -x company=be67ce39 upgrade head      # specific company DB
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context
import sys, os

# Ensure backend is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url from settings.
# Alembic uses ConfigParser interpolation, so literal '%' in passwords must be escaped.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

target_metadata = None  # We use raw SQL migrations, not ORM models


def _get_company_urls():
    """Get list of company database URLs to migrate."""
    company_arg = context.get_x_argument(as_dictionary=True).get("company", None)

    if not company_arg:
        return []  # Only system DB

    from sqlalchemy import create_engine
    eng = create_engine(settings.DATABASE_URL)

    if company_arg == "all":
        with eng.connect() as conn:
            rows = conn.execute(text("SELECT id FROM system_companies WHERE status = 'active'")).fetchall()
        eng.dispose()
        return [settings.get_company_database_url(r[0]) for r in rows]
    else:
        eng.dispose()
        return [settings.get_company_database_url(company_arg)]


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    # 1. Run on system DB
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    # 2. Run on company DBs (if requested)
    for url in _get_company_urls():
        from sqlalchemy import create_engine
        eng = create_engine(url, poolclass=pool.NullPool)
        try:
            with eng.connect() as connection:
                context.configure(connection=connection, target_metadata=target_metadata)
                with context.begin_transaction():
                    context.run_migrations()
        except Exception as e:
            print(f"⚠️ Migration failed for {url}: {e}")
        finally:
            eng.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
