import logging
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text
from datetime import datetime, timedelta, date

from database import engine as system_engine, _get_engine
from utils.email import send_email
from utils.exports import generate_pdf, generate_excel
from routers.reports import _get_profit_loss_data, _get_balance_sheet_data

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _get_company_engine_for_db(db_name: str):
    """Get a cached engine for a company DB by database name."""
    # Extract company_id from db_name (format: aman_{company_id})
    company_id = db_name.replace("aman_", "", 1)
    if company_id == "system":
        return system_engine
    return _get_engine(company_id)

def flatten_report_data(data_nodes):
    """Flatten hierarchical data for export"""
    flat_data = []
    
    def _flatten(nodes, indent=0):
        for node in nodes:
            flat_data.append({
                "Account Number": node.get("account_number", ""),
                "Account Name": f"{'  ' * indent}{node.get('name', '')}",
                "Balance": f"{float(node.get('balance', 0)):,.2f}",
                "Type": node.get("account_type", "")
            })
            if node.get("children"):
                _flatten(node["children"], indent + 1)
                
    _flatten(data_nodes)
    return flat_data

def process_scheduled_report(conn, report):
    try:
        report_id = report.id
        report_type = report.report_type
        branch_id = report.branch_id
        recipients = report.recipients.split(',')
        fmt = report.format or 'pdf'
        
        logger.info(f"⚙️ Processing report {report_id} ({report_type}) for branch {branch_id}")
        
        # Generate Data
        today = date.today()
        # Determined date range based on report type/frequency?
        # For now, default to 'This Month' or 'YTD'. Let's assume YTD for now or simple Month.
        # Ideally, scheduled report should have params for date range (e.g. 'last_month', 'ytd').
        # Using YTD for simplicity: Jan 1 to Today.
        start_date = today.replace(day=1, month=1)
        end_date = today
        
        filename = f"{report_type}_{today}.{fmt}"
        file_data = None
        
        if report_type == 'profit_loss':
            data = _get_profit_loss_data(conn, start_date, end_date, branch_id)
            flat = flatten_report_data(data["data"])
            # Add Total
            flat.append({
                "Account Number": "",
                "Account Name": "Net Income / صافي الدخل",
                "Balance": f"{float(data.get('total', 0)):,.2f}",
                "Type": ""
            })
            
            if fmt == 'excel':
                file_data = generate_excel(flat, ["Account Number", "Account Name", "Balance"]).read()
            else:
                pdf_rows = [["Account #", "Account Name", "Balance"]]
                for r in flat:
                    pdf_rows.append([r["Account Number"], r["Account Name"], r["Balance"]])
                file_data = generate_pdf(pdf_rows, f"Profit & Loss ({start_date} - {end_date})").read()

        elif report_type == 'balance_sheet':
            data = _get_balance_sheet_data(conn, end_date, branch_id)
            flat = flatten_report_data(data["data"])
            
            if fmt == 'excel':
                file_data = generate_excel(flat, ["Account Number", "Account Name", "Balance"]).read()
            else:
                pdf_rows = [["Account #", "Account Name", "Balance"]]
                for r in flat:
                    pdf_rows.append([r["Account Number"], r["Account Name"], r["Balance"]])
                file_data = generate_pdf(pdf_rows, f"Balance Sheet (As of {end_date})").read()
        
        if file_data:
            subject = f"Scheduled Report: {report_type.replace('_', ' ').title()}"
            body = f"Please find attached the {report_type} report for {today}."
            
            attachments = [{
                "filename": filename,
                "data": file_data,
                "content_type": "application/pdf" if fmt == 'pdf' else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }]
            
            sent = send_email(recipients, subject, body, attachments)
            
            if sent:
                # Update next_run
                next_run = datetime.now()
                if report.frequency == 'daily':
                    next_run += timedelta(days=1)
                elif report.frequency == 'weekly':
                    next_run += timedelta(weeks=1)
                elif report.frequency == 'monthly':
                    next_run += timedelta(days=30) # approx
                else:
                    next_run += timedelta(days=1)
                
                conn.execute(text("UPDATE scheduled_reports SET last_run_at = NOW(), next_run_at = :next WHERE id = :id"), {"next": next_run, "id": report_id})
                conn.commit()
                logger.info(f"✅ Report {report_id} processed and updated.")
            else:
                logger.warning(f"⚠️ Report {report_id} generated but email failed.")
        
    except Exception as e:
        logger.error(f"❌ Error processing report {report.id}: {e}")

def check_scheduled_reports():
    """Check all databases for due reports"""
    logger.info("⏰ Checking scheduled reports...")
    
    databases = []
    try:
        with system_engine.connect() as conn:
            result = conn.execute(text("SELECT datname FROM pg_database WHERE datname LIKE 'aman_%'"))
            databases = [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.error(f"❌ Failed to list DBs: {e}")
        return
        
    for db_name in databases:
        try:
            # Connect to company DB
            engine = _get_company_engine_for_db(db_name)
            
            with engine.connect() as conn:
                reports = conn.execute(text("SELECT * FROM scheduled_reports WHERE is_active = TRUE AND (next_run_at <= NOW() OR next_run_at IS NULL)")).fetchall()
                
                for report in reports:
                    process_scheduled_report(conn, report)
                    
        except Exception as e:
            logger.error(f"❌ Error checking DB {db_name}: {e}")


MATERIALIZED_VIEWS = [
    "mv_revenue_summary",
    "mv_expense_summary",
    "mv_cash_position",
    "mv_top_customers",
    "mv_ar_aging",
    "mv_ap_aging",
    "mv_inventory_turnover",
    "mv_sales_pipeline",
]


def refresh_analytics_materialized_views():
    """Refresh all BI analytics materialized views across company databases."""
    logger.info("⏰ Refreshing analytics materialized views...")

    databases = []
    try:
        with system_engine.connect() as conn:
            result = conn.execute(text("SELECT datname FROM pg_database WHERE datname LIKE 'aman_%'"))
            databases = [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.error(f"❌ Failed to list DBs for MV refresh: {e}")
        return

    for db_name in databases:
        try:
            engine = _get_company_engine_for_db(db_name)

            with engine.connect() as conn:
                for mv_name in MATERIALIZED_VIEWS:
                    try:
                        # Check if the materialized view exists before refreshing
                        exists = conn.execute(
                            text("SELECT EXISTS (SELECT 1 FROM pg_matviews WHERE matviewname = :name)"),
                            {"name": mv_name}
                        ).scalar()
                        if exists:
                            conn.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {mv_name}"))
                            conn.commit()
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to refresh {mv_name} in {db_name}: {e}")

                logger.info(f"✅ Refreshed materialized views in {db_name}")
        except Exception as e:
            logger.error(f"❌ Error refreshing MVs in {db_name}: {e}")


def check_subscription_billing():
    """Check all company databases for subscription billing due, trial expirations, and retries."""
    logger.info("⏰ Checking subscription billing...")

    databases = []
    try:
        with system_engine.connect() as conn:
            result = conn.execute(text("SELECT datname FROM pg_database WHERE datname LIKE 'aman_%'"))
            databases = [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.error(f"❌ Failed to list DBs for subscription billing: {e}")
        return

    from services.subscription_service import check_billing_due, check_trial_expirations

    for db_name in databases:
        try:
            engine = _get_company_engine_for_db(db_name)

            with engine.connect() as conn:
                # Check if subscription tables exist
                has_table = conn.execute(
                    text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'subscription_enrollments')")
                ).scalar()
                if not has_table:
                    continue

                # 1. Check trial expirations
                try:
                    converted = check_trial_expirations(conn)
                    if converted > 0:
                        logger.info(f"✅ Converted {converted} trials in {db_name}")
                except Exception as e:
                    logger.error(f"❌ Trial check failed in {db_name}: {e}")

                # 2. Generate due invoices
                try:
                    results = check_billing_due(conn, user="system")
                    if results:
                        logger.info(f"✅ Generated {len(results)} subscription invoices in {db_name}")
                except Exception as e:
                    logger.error(f"❌ Billing check failed in {db_name}: {e}")

        except Exception as e:
            logger.error(f"❌ Error checking subscription billing in {db_name}: {e}")


def archive_old_audit_logs():
    """T018: Archive audit log entries older than 1 year, delete entries older than 7 years."""
    logger.info("⏰ Running audit log archival job...")

    databases = []
    try:
        with system_engine.connect() as conn:
            result = conn.execute(text("SELECT datname FROM pg_database WHERE datname LIKE 'aman_%'"))
            databases = [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Failed to list DBs for audit archival: {e}")
        return

    for db_name in databases:
        try:
            company_engine = _get_company_engine_for_db(db_name)

            with company_engine.connect() as conn:
                # Check if is_archived column exists
                has_col = conn.execute(text(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                    "WHERE table_name = 'audit_logs' AND column_name = 'is_archived')"
                )).scalar()
                if not has_col:
                    continue

                # Archive entries older than 1 year
                archived = conn.execute(text(
                    "UPDATE audit_logs SET is_archived = TRUE, archived_at = NOW() "
                    "WHERE created_at < NOW() - INTERVAL '1 year' AND (is_archived IS NULL OR is_archived = FALSE)"
                ))
                conn.commit()

                # Delete entries older than 7 years
                deleted = conn.execute(text(
                    "DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '7 years'"
                ))
                conn.commit()

                if archived.rowcount > 0 or deleted.rowcount > 0:
                    logger.info(f"Audit archival in {db_name}: archived={archived.rowcount}, deleted={deleted.rowcount}")
        except Exception as e:
            logger.error(f"Error archiving audit logs in {db_name}: {e}")


def retry_failed_notifications():
    """T019: Retry failed notifications with exponential backoff (1min/5min/30min)."""
    logger.info("⏰ Running notification retry job...")

    # Backoff intervals in seconds by retry_count
    backoff_seconds = {0: 60, 1: 300, 2: 1800}

    databases = []
    try:
        with system_engine.connect() as conn:
            result = conn.execute(text("SELECT datname FROM pg_database WHERE datname LIKE 'aman_%'"))
            databases = [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Failed to list DBs for notification retry: {e}")
        return

    for db_name in databases:
        try:
            company_engine = _get_company_engine_for_db(db_name)

            with company_engine.connect() as conn:
                # Check if delivery_status column exists
                has_col = conn.execute(text(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                    "WHERE table_name = 'notifications' AND column_name = 'delivery_status')"
                )).scalar()
                if not has_col:
                    continue

                # Find failed notifications eligible for retry
                failed = conn.execute(text(
                    "SELECT id, user_id, title, message, type, retry_count, delivery_channel "
                    "FROM notifications "
                    "WHERE delivery_status = 'failed' AND retry_count < 3 "
                    "AND (last_retry_at IS NULL OR last_retry_at < NOW() - INTERVAL '1 second' * :backoff)"
                ), {"backoff": 60}).fetchall()

                for notif in failed:
                    retry_count = notif.retry_count or 0
                    required_backoff = backoff_seconds.get(retry_count, 1800)

                    # Check actual backoff
                    eligible = conn.execute(text(
                        "SELECT 1 FROM notifications WHERE id = :id "
                        "AND (last_retry_at IS NULL OR last_retry_at < NOW() - INTERVAL '1 second' * :backoff)"
                    ), {"id": notif.id, "backoff": required_backoff}).fetchone()

                    if not eligible:
                        continue

                    # Attempt re-delivery (email channel)
                    try:
                        if notif.delivery_channel == 'email':
                            # Get user email
                            user_row = conn.execute(text(
                                "SELECT email FROM company_users WHERE id = :uid"
                            ), {"uid": notif.user_id}).fetchone()
                            if user_row and user_row.email:
                                send_email([user_row.email], notif.title or "Notification", notif.message or "")

                        # Mark as delivered
                        conn.execute(text(
                            "UPDATE notifications SET delivery_status = 'delivered', "
                            "retry_count = :rc, last_retry_at = NOW() WHERE id = :id"
                        ), {"rc": retry_count + 1, "id": notif.id})
                        conn.commit()
                    except Exception:
                        new_count = retry_count + 1
                        new_status = 'permanently_failed' if new_count >= 3 else 'failed'
                        conn.execute(text(
                            "UPDATE notifications SET delivery_status = :status, "
                            "retry_count = :rc, last_retry_at = NOW() WHERE id = :id"
                        ), {"status": new_status, "rc": new_count, "id": notif.id})
                        conn.commit()
                        logger.warning(f"Notification {notif.id} retry {new_count} failed in {db_name}")

        except Exception as e:
            logger.error(f"Error retrying notifications in {db_name}: {e}")


def start_scheduler():
    scheduler.add_job(check_scheduled_reports, 'interval', minutes=5, id='scheduled_reports',
                      max_instances=1, coalesce=True, misfire_grace_time=60)
    scheduler.add_job(check_subscription_billing, 'interval', hours=24, id='subscription_billing',
                      max_instances=1, coalesce=True, misfire_grace_time=60)
    scheduler.add_job(refresh_analytics_materialized_views, 'interval', minutes=15, id='analytics_mv_refresh',
                      max_instances=1, coalesce=True, misfire_grace_time=60)
    scheduler.add_job(archive_old_audit_logs, 'interval', hours=24, id='audit_archival',
                      max_instances=1, coalesce=True, misfire_grace_time=60)  # Daily
    scheduler.add_job(retry_failed_notifications, 'interval', minutes=1, id='notification_retry',
                      max_instances=1, coalesce=True, misfire_grace_time=60)  # Every minute
    scheduler.start()
    logger.info("🚀 Scheduler started.")
