import logging
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta, date

from config import settings
from utils.email import send_email
from utils.exports import generate_pdf, generate_excel
from routers.reports import _get_profit_loss_data, _get_balance_sheet_data

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def get_system_engine():
    return create_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")

def get_company_engine(company_db_url):
    return create_engine(company_db_url, isolation_level="AUTOCOMMIT")

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
    sys_engine = get_system_engine()
    
    databases = []
    try:
        with sys_engine.connect() as conn:
            result = conn.execute(text("SELECT datname FROM pg_database WHERE datname LIKE 'aman_%'"))
            databases = [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.error(f"❌ Failed to list DBs: {e}")
        return
        
    for db_name in databases:
        try:
            # Connect to company DB
            base_url = settings.DATABASE_URL.rsplit('/', 1)[0]
            company_url = f"{base_url}/{db_name}"
            engine = get_company_engine(company_url)
            
            with engine.connect() as conn:
                reports = conn.execute(text("SELECT * FROM scheduled_reports WHERE is_active = TRUE AND (next_run_at <= NOW() OR next_run_at IS NULL)")).fetchall()
                
                for report in reports:
                    process_scheduled_report(conn, report)
                    
        except Exception as e:
            logger.error(f"❌ Error checking DB {db_name}: {e}")

def start_scheduler():
    scheduler.add_job(check_scheduled_reports, 'interval', minutes=5) # Run every 5 mins
    scheduler.start()
    logger.info("🚀 Scheduler started.")
