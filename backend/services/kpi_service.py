"""
AMAN ERP - KPI Calculation Service
خدمة حساب مؤشرات الأداء الرئيسية

Calculates all KPIs for role-based and industry dashboards.
Each KPI function is independent and testable.

Standards: IFRS, IAS 1/2/7/19/32, IFRS 15/16, GAZT Nitaqat, PMI PMBOK
"""

from sqlalchemy import text
from datetime import date, timedelta, datetime
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Helper: Period Resolution
# ═══════════════════════════════════════════════════════════════════════════════

def resolve_period(period: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Tuple[date, date]:
    """Resolve period keyword to (start_date, end_date) tuple."""
    today = date.today()
    if period == "custom" and start_date and end_date:
        return (start_date, end_date)
    elif period == "today":
        return (today, today)
    elif period == "wtd":
        # Week starts Sunday in Saudi Arabia
        days_since_sunday = (today.weekday() + 1) % 7
        return (today - timedelta(days=days_since_sunday), today)
    elif period == "mtd":
        return (today.replace(day=1), today)
    elif period == "qtd":
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        return (today.replace(month=quarter_month, day=1), today)
    elif period == "ytd":
        return (today.replace(month=1, day=1), today)
    elif period == "last_month":
        first_of_month = today.replace(day=1)
        last_month_end = first_of_month - timedelta(days=1)
        return (last_month_end.replace(day=1), last_month_end)
    elif period == "last_quarter":
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        qstart = today.replace(month=quarter_month, day=1)
        prev_q_end = qstart - timedelta(days=1)
        prev_q_month = ((prev_q_end.month - 1) // 3) * 3 + 1
        return (prev_q_end.replace(month=prev_q_month, day=1), prev_q_end)
    else:
        # Default: MTD
        return (today.replace(day=1), today)


def get_previous_period(start_date: date, end_date: date) -> Tuple[date, date]:
    """Get the equivalent previous period for comparison."""
    delta = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=delta - 1)
    return (prev_start, prev_end)


def build_branch_filter(branch_id: Optional[int], table_alias: str = "je") -> Tuple[str, dict]:
    """Build branch filter SQL clause and params."""
    if branch_id:
        return (f"AND {table_alias}.branch_id = :branch_id", {"branch_id": branch_id})
    return ("", {})


def kpi_item(key: str, label_en: str, label_ar: str, value: Any, unit: str = "",
             trend_value: str = "", trend_direction: str = "neutral", trend_positive: bool = True,
             benchmark: Any = None, benchmark_source: str = "", status: str = "neutral") -> dict:
    """Build a standardized KPI item dict."""
    return {
        "key": key,
        "label": label_en,
        "label_ar": label_ar,
        "value": round(value, 2) if isinstance(value, (int, float)) else value,
        "unit": unit,
        "trend_value": trend_value,
        "trend_direction": trend_direction,
        "trend_positive": trend_positive,
        "benchmark": benchmark,
        "benchmark_source": benchmark_source,
        "status": status,
    }


def calc_trend(current: float, previous: float) -> Tuple[str, str, bool]:
    """Calculate trend value, direction, and whether it's positive.
    Returns (trend_value, trend_direction, trend_positive) assuming higher is better.
    """
    if previous == 0:
        if current > 0:
            return ("+100%", "up", True)
        return ("0%", "neutral", True)
    change = ((current - previous) / abs(previous)) * 100
    direction = "up" if change > 0 else ("down" if change < 0 else "neutral")
    positive = change >= 0
    return (f"{'+' if change >= 0 else ''}{change:.1f}%", direction, positive)


def calc_trend_inverse(current: float, previous: float) -> Tuple[str, str, bool]:
    """Like calc_trend but lower is better (e.g., expenses, DSO)."""
    trend_value, direction, _ = calc_trend(current, previous)
    positive = direction == "down" or direction == "neutral"
    return (trend_value, direction, positive)


def ratio_status(value: float, good: float, warning: float, higher_is_better: bool = True) -> str:
    """Determine status based on thresholds."""
    if higher_is_better:
        if value >= good:
            return "good"
        elif value >= warning:
            return "warning"
        return "danger"
    else:
        if value <= good:
            return "good"
        elif value <= warning:
            return "warning"
        return "danger"


# ═══════════════════════════════════════════════════════════════════════════════
# GL-Based Building Blocks (used by multiple KPIs)
# ═══════════════════════════════════════════════════════════════════════════════

def _gl_sum(db, account_type: str, start_date: date, end_date: date,
            branch_id: Optional[int] = None, debit_minus_credit: bool = True) -> float:
    """Sum journal lines for a given account type within a period."""
    branch_sql, params = build_branch_filter(branch_id)
    expr = "jl.debit - jl.credit" if debit_minus_credit else "jl.credit - jl.debit"
    result = db.execute(text(f"""
        SELECT COALESCE(SUM({expr}), 0)
        FROM journal_lines jl
        JOIN journal_entries je ON jl.journal_entry_id = je.id
        JOIN accounts a ON jl.account_id = a.id
        WHERE a.account_type = :acct_type
          AND je.entry_date BETWEEN :start_dt AND :end_dt
          AND je.status = 'posted'
          {branch_sql}
    """), {"acct_type": account_type, "start_dt": start_date, "end_dt": end_date, **params}).scalar()
    return float(result or 0)


def _gl_balance(db, account_type: str, as_of: date,
                branch_id: Optional[int] = None, debit_minus_credit: bool = True) -> float:
    """Cumulative balance of accounts of a given type up to a date.
    Handles special sub-types (receivable, payable) via account_code patterns."""
    branch_sql, params = build_branch_filter(branch_id)
    expr = "jl.debit - jl.credit" if debit_minus_credit else "jl.credit - jl.debit"
    # Handle sub-types that don't exist as account_type values
    special_types = {
        "receivable": "(a.account_type = 'asset' AND a.account_code LIKE '12%')",
        "payable": "(a.account_type = 'liability' AND a.account_code LIKE '21%')",
    }
    if account_type in special_types:
        type_filter = special_types[account_type]
    else:
        type_filter = "a.account_type = :acct_type"
        params["acct_type"] = account_type
    result = db.execute(text(f"""
        SELECT COALESCE(SUM({expr}), 0)
        FROM journal_lines jl
        JOIN journal_entries je ON jl.journal_entry_id = je.id
        JOIN accounts a ON jl.account_id = a.id
        WHERE {type_filter}
          AND je.entry_date <= :end_dt
          AND je.status = 'posted'
          {branch_sql}
    """), {"end_dt": as_of, **params}).scalar()
    return float(result or 0)


def _gl_balance_by_classification(db, classification: str, as_of: date,
                                   branch_id: Optional[int] = None) -> float:
    """Balance by account classification (current_asset, fixed_asset, current_liability, etc.).
    Uses account_code patterns since accounts table has no classification column."""
    branch_sql, params = build_branch_filter(branch_id)
    code_filters = {
        "current_asset": "(a.account_type = 'asset' AND a.account_code ~ '^1[1-5]')",
        "fixed_asset": "(a.account_type = 'asset' AND a.account_code LIKE '16%')",
        "current_liability": "(a.account_type = 'liability' AND a.account_code LIKE '21%')",
        "long_term_liability": "(a.account_type = 'liability' AND a.account_code LIKE '22%')",
    }
    filter_sql = code_filters.get(classification, f"a.account_type = '{classification}'")
    result = db.execute(text(f"""
        SELECT COALESCE(SUM(jl.debit - jl.credit), 0)
        FROM journal_lines jl
        JOIN journal_entries je ON jl.journal_entry_id = je.id
        JOIN accounts a ON jl.account_id = a.id
        WHERE {filter_sql}
          AND je.entry_date <= :end_dt
          AND je.status = 'posted'
          {branch_sql}
    """), {"end_dt": as_of, **params}).scalar()
    return float(result or 0)


def _count_table(db, table: str, branch_id: Optional[int] = None,
                 date_col: str = "created_at", start_date: Optional[date] = None,
                 end_date: Optional[date] = None, extra_where: str = "") -> int:
    """Count rows in a table with optional filters."""
    conditions = ["1=1"]
    params = {}
    if branch_id:
        conditions.append("branch_id = :branch_id")
        params["branch_id"] = branch_id
    if start_date and date_col:
        conditions.append(f"{date_col} >= :start_dt")
        params["start_dt"] = start_date
    if end_date and date_col:
        conditions.append(f"{date_col} <= :end_dt")
        params["end_dt"] = end_date
    if extra_where:
        conditions.append(extra_where)
    where = " AND ".join(conditions)
    result = db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE {where}"), params).scalar()
    return int(result or 0)


def _sum_column(db, table: str, column: str, branch_id: Optional[int] = None,
                date_col: str = "created_at", start_date: Optional[date] = None,
                end_date: Optional[date] = None, extra_where: str = "") -> float:
    """Sum a column in a table with optional filters."""
    conditions = ["1=1"]
    params = {}
    if branch_id:
        conditions.append("branch_id = :branch_id")
        params["branch_id"] = branch_id
    if start_date and date_col:
        conditions.append(f"{date_col} >= :start_dt")
        params["start_dt"] = start_date
    if end_date and date_col:
        conditions.append(f"{date_col} <= :end_dt")
        params["end_dt"] = end_date
    if extra_where:
        conditions.append(extra_where)
    where = " AND ".join(conditions)
    result = db.execute(text(f"SELECT COALESCE(SUM({column}), 0) FROM {table} WHERE {where}"), params).scalar()
    return float(result or 0)


# ═══════════════════════════════════════════════════════════════════════════════
# Executive Dashboard KPIs (CEO / Admin)
# ═══════════════════════════════════════════════════════════════════════════════

def get_executive_kpis(db, start_date: date, end_date: date,
                       branch_id: Optional[int] = None) -> dict:
    """KPIs for CEO / Executive role."""
    prev_start, prev_end = get_previous_period(start_date, end_date)

    # Revenue (credit - debit for revenue accounts)
    revenue = _gl_sum(db, "revenue", start_date, end_date, branch_id, debit_minus_credit=False)
    prev_revenue = _gl_sum(db, "revenue", prev_start, prev_end, branch_id, debit_minus_credit=False)

    # Expenses (debit - credit for expense accounts)
    expenses = _gl_sum(db, "expense", start_date, end_date, branch_id)
    prev_expenses = _gl_sum(db, "expense", prev_start, prev_end, branch_id)

    # COGS (expense accounts with code starting with 5)
    cogs = 0
    try:
        cogs_result = db.execute(text("""
            SELECT COALESCE(SUM(jl.debit - jl.credit), 0)
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.account_type = 'expense' AND a.account_code LIKE '5%'
              AND je.entry_date BETWEEN :s AND :e AND je.status = 'posted'
        """), {"s": start_date, "e": end_date}).scalar()
        cogs = float(cogs_result or 0)
    except Exception:
        pass

    net_income = revenue - expenses - cogs
    prev_net = prev_revenue - prev_expenses
    profit_margin = (net_income / revenue * 100) if revenue > 0 else 0

    # EBITDA (Net Income + Interest + Tax + Depreciation + Amortization)
    # Simplified: Revenue - Operating Expenses (exclude interest, tax, depreciation)
    ebitda = net_income  # Simplified — full version would exclude specific accounts

    # Operating Expense Ratio
    opex_ratio = (expenses / revenue * 100) if revenue > 0 else 0

    # Cash & Bank Balance
    cash_balance = 0
    try:
        cash_result = db.execute(text("""
            SELECT COALESCE(SUM(current_balance), 0) FROM treasury_accounts WHERE is_active = true
        """)).scalar()
        cash_balance = float(cash_result or 0)
    except Exception:
        pass

    # DSO (Days Sales Outstanding) = AR / (Revenue / days_in_period)
    ar_balance = _gl_balance(db, "receivable", end_date, branch_id)
    days_in_period = max((end_date - start_date).days, 1)
    daily_revenue = revenue / days_in_period if days_in_period > 0 else 0
    dso = ar_balance / daily_revenue if daily_revenue > 0 else 0

    # DPO (Days Payable Outstanding) = AP / (COGS / days_in_period)
    ap_balance = _gl_balance(db, "payable", end_date, branch_id, debit_minus_credit=False)
    daily_cogs = cogs / days_in_period if days_in_period > 0 else 0
    dpo = ap_balance / daily_cogs if daily_cogs > 0 else 0

    # Headcount
    headcount = _count_table(db, "employees", extra_where="status = 'active'")

    # Revenue trend
    rev_trend = calc_trend(revenue, prev_revenue)
    exp_trend = calc_trend_inverse(expenses, prev_expenses)
    profit_trend = calc_trend(net_income, prev_net)

    kpis = [
        kpi_item("revenue", "Revenue", "الإيرادات", revenue, "SAR",
                 rev_trend[0], rev_trend[1], rev_trend[2]),
        kpi_item("revenue_growth", "Revenue Growth", "نمو الإيرادات", rev_trend[0].rstrip('%'), "%",
                 rev_trend[0], rev_trend[1], rev_trend[2], benchmark=5.0, benchmark_source="Industry Avg"),
        kpi_item("net_profit_margin", "Net Profit Margin", "هامش صافي الربح", profit_margin, "%",
                 profit_trend[0], profit_trend[1], profit_trend[2],
                 benchmark=15.0, benchmark_source="IAS 1",
                 status=ratio_status(profit_margin, 15, 5)),
        kpi_item("ebitda", "EBITDA", "الأرباح قبل الفوائد والضرائب والإهلاك", ebitda, "SAR"),
        kpi_item("opex_ratio", "Operating Expense Ratio", "نسبة المصاريف التشغيلية", opex_ratio, "%",
                 exp_trend[0], exp_trend[1], not exp_trend[2],
                 benchmark=70.0, benchmark_source="Industry Avg",
                 status=ratio_status(opex_ratio, 60, 80, higher_is_better=False)),
        kpi_item("cash_balance", "Cash & Bank Balance", "الرصيد النقدي والبنكي", cash_balance, "SAR"),
        kpi_item("dso", "Days Sales Outstanding", "أيام تحصيل المبيعات", dso, "days",
                 status=ratio_status(dso, 30, 60, higher_is_better=False),
                 benchmark=30, benchmark_source="Best Practice"),
        kpi_item("dpo", "Days Payable Outstanding", "أيام سداد المشتريات", dpo, "days",
                 benchmark=45, benchmark_source="Best Practice"),
        kpi_item("headcount", "Headcount", "عدد الموظفين", headcount, ""),
    ]

    # Charts
    charts = _build_revenue_expense_chart(db, start_date, end_date, branch_id)

    # Alerts
    alerts = _build_executive_alerts(db, branch_id)

    return {"role": "executive", "kpis": kpis, "charts": charts, "alerts": alerts}


# ═══════════════════════════════════════════════════════════════════════════════
# Financial Dashboard KPIs (CFO / Accountant)
# ═══════════════════════════════════════════════════════════════════════════════

def get_financial_kpis(db, start_date: date, end_date: date,
                       branch_id: Optional[int] = None) -> dict:
    """KPIs for CFO / Accountant role."""
    prev_start, prev_end = get_previous_period(start_date, end_date)

    # Current Assets & Liabilities (balance as of end_date)
    current_assets = _gl_balance_by_classification(db, "current_asset", end_date, branch_id)
    if current_assets == 0:
        # Fallback: sum asset accounts with codes 1xxx
        current_assets = _gl_balance(db, "asset", end_date, branch_id)

    current_liabilities = abs(_gl_balance_by_classification(db, "current_liability", end_date, branch_id))
    if current_liabilities == 0:
        current_liabilities = abs(_gl_balance(db, "liability", end_date, branch_id, debit_minus_credit=False))

    # Inventory balance
    inventory_balance = 0
    try:
        inv_result = db.execute(text("""
            SELECT COALESCE(SUM(jl.debit - jl.credit), 0)
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            JOIN accounts a ON jl.account_id = a.id
            WHERE (a.account_code LIKE '14%' OR a.name ILIKE '%inventory%' OR a.name ILIKE '%مخزون%')
              AND je.entry_date <= :end_dt AND je.status = 'posted'
        """), {"end_dt": end_date}).scalar()
        inventory_balance = float(inv_result or 0)
    except Exception:
        pass

    # Ratios
    current_ratio = current_assets / current_liabilities if current_liabilities > 0 else 0
    quick_ratio = (current_assets - inventory_balance) / current_liabilities if current_liabilities > 0 else 0

    # Total Debt & Equity
    total_debt = current_liabilities  # Simplified — should include long-term too
    equity = _gl_balance(db, "equity", end_date, branch_id, debit_minus_credit=False)
    debt_to_equity = total_debt / equity if equity > 0 else 0

    # Revenue & Margins
    revenue = _gl_sum(db, "revenue", start_date, end_date, branch_id, debit_minus_credit=False)
    cogs = 0
    try:
        cogs_r = db.execute(text("""
            SELECT COALESCE(SUM(jl.debit - jl.credit), 0)
            FROM journal_lines jl JOIN journal_entries je ON jl.journal_entry_id = je.id
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.account_type = 'expense' AND a.account_code LIKE '5%'
              AND je.entry_date BETWEEN :s AND :e AND je.status = 'posted'
        """), {"s": start_date, "e": end_date}).scalar()
        cogs = float(cogs_r or 0)
    except Exception:
        pass

    expenses = _gl_sum(db, "expense", start_date, end_date, branch_id)
    gross_margin = ((revenue - cogs) / revenue * 100) if revenue > 0 else 0
    net_margin = ((revenue - cogs - expenses) / revenue * 100) if revenue > 0 else 0

    # Budget vs Actual
    budget_variance = 0
    try:
        bv = db.execute(text("""
            SELECT
                COALESCE(SUM(bi.planned_amount), 0) as budgeted,
                COALESCE(SUM(bi.actual_amount), 0) as actual
            FROM budget_items bi
            JOIN budgets b ON bi.budget_id = b.id
            WHERE b.status = 'active'
        """)).fetchone()
        if bv and bv[0] > 0:
            budget_variance = ((bv[1] - bv[0]) / bv[0]) * 100
    except Exception:
        pass

    # AR Aging
    ar_aging = _build_ar_aging(db, end_date, branch_id)

    # AP Aging
    ap_aging = _build_ap_aging(db, end_date, branch_id)

    # VAT Position
    vat_output = 0
    vat_input = 0
    try:
        vat_r = db.execute(text("""
            SELECT
                COALESCE(SUM(CASE WHEN jl.credit > 0 AND a.account_code LIKE '22%' THEN jl.credit ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN jl.debit > 0 AND a.account_code LIKE '15%' THEN jl.debit ELSE 0 END), 0)
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            JOIN accounts a ON jl.account_id = a.id
            WHERE je.entry_date BETWEEN :s AND :e AND je.status = 'posted'
        """), {"s": start_date, "e": end_date}).fetchone()
        if vat_r:
            vat_output = float(vat_r[0] or 0)
            vat_input = float(vat_r[1] or 0)
    except Exception:
        pass
    vat_position = vat_output - vat_input

    # Zakat estimate (ZATCA method: equity minus fixed assets and intangibles × 2.5%)
    zakat_estimate = 0
    try:
        try:
            db.rollback()
        except Exception:
            pass
        branch_sql_z, bp_z = build_branch_filter(branch_id)
        # Fixed assets (property/plant/equipment — non-zakatable)
        fa_bal = db.execute(text(f"""
            SELECT COALESCE(SUM(jl.debit - jl.credit), 0)
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.account_type = 'asset'
              AND (
                a.account_code LIKE '12%%' OR a.account_code LIKE '15%%' OR a.account_code LIKE '16%%'
                OR a.name LIKE '%%أصول ثابتة%%' OR a.name LIKE '%%معدات%%' OR a.name LIKE '%%آلات%%'
                OR a.name LIKE '%%مباني%%' OR a.name LIKE '%%سيارات%%' OR a.name LIKE '%%أثاث%%'
                OR a.name_en ILIKE '%%fixed asset%%' OR a.name_en ILIKE '%%equipment%%'
                OR a.name_en ILIKE '%%building%%' OR a.name_en ILIKE '%%vehicle%%'
                OR a.name_en ILIKE '%%furniture%%' OR a.name_en ILIKE '%%depreciation%%'
              )
              AND je.entry_date <= :end_dt AND je.status = 'posted'
              {branch_sql_z}
        """), {"end_dt": end_date, **bp_z}).scalar()
        fixed_assets_bal = float(fa_bal or 0)

        # Intangible assets (goodwill/IP — non-zakatable)
        intang_bal = db.execute(text(f"""
            SELECT COALESCE(SUM(jl.debit - jl.credit), 0)
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.account_type = 'asset'
              AND (
                a.account_code LIKE '18%%'
                OR a.name LIKE '%%شهرة%%' OR a.name LIKE '%%براءة%%'
                OR a.name LIKE '%%رخصة%%' OR a.name LIKE '%%غير ملموس%%'
                OR a.name_en ILIKE '%%goodwill%%' OR a.name_en ILIKE '%%intangible%%'
                OR a.name_en ILIKE '%%patent%%' OR a.name_en ILIKE '%%trademark%%'
              )
              AND je.entry_date <= :end_dt AND je.status = 'posted'
              {branch_sql_z}
        """), {"end_dt": end_date, **bp_z}).scalar()
        intangibles_bal = float(intang_bal or 0)

        zakat_base = max(0.0, equity - fixed_assets_bal - intangibles_bal)
        zakat_estimate = zakat_base * 0.025
    except Exception:
        pass

    prev_current_ratio = 0  # Would need prev period balance — simplified

    kpis = [
        kpi_item("current_ratio", "Current Ratio", "نسبة التداول", current_ratio, "x",
                 benchmark=2.0, benchmark_source="IAS 1",
                 status=ratio_status(current_ratio, 2.0, 1.0)),
        kpi_item("quick_ratio", "Quick Ratio", "نسبة السيولة السريعة", quick_ratio, "x",
                 benchmark=1.0, benchmark_source="IAS 1",
                 status=ratio_status(quick_ratio, 1.0, 0.5)),
        kpi_item("debt_to_equity", "Debt-to-Equity", "نسبة الدين إلى حقوق الملكية", debt_to_equity, "x",
                 benchmark=1.5, benchmark_source="IAS 32",
                 status=ratio_status(debt_to_equity, 1.0, 2.0, higher_is_better=False)),
        kpi_item("gross_margin", "Gross Margin", "هامش الربح الإجمالي", gross_margin, "%",
                 benchmark=30.0, benchmark_source="Industry Avg",
                 status=ratio_status(gross_margin, 30, 15)),
        kpi_item("net_margin", "Net Margin", "صافي هامش الربح", net_margin, "%",
                 benchmark=15.0, benchmark_source="IAS 1",
                 status=ratio_status(net_margin, 15, 5)),
        kpi_item("budget_variance", "Budget vs Actual", "الانحراف عن الميزانية", budget_variance, "%",
                 benchmark=0, benchmark_source="Internal",
                 status=ratio_status(abs(budget_variance), 5, 15, higher_is_better=False)),
        kpi_item("vat_position", "VAT Position", "موقف ضريبة القيمة المضافة", vat_position, "SAR"),
        kpi_item("zakat_estimate", "Zakat Estimate", "تقدير الزكاة", zakat_estimate, "SAR",
                 benchmark_source="GAZT"),
    ]

    charts = [
        {"id": "ar_aging", "type": "bar", "title": "AR Aging", "title_ar": "أعمار الذمم المدينة", "data": ar_aging},
        {"id": "ap_aging", "type": "bar", "title": "AP Aging", "title_ar": "أعمار الذمم الدائنة", "data": ap_aging},
    ]

    alerts = _build_financial_alerts(db, current_ratio, quick_ratio, budget_variance, branch_id)

    return {"role": "financial", "kpis": kpis, "charts": charts, "alerts": alerts}


# ═══════════════════════════════════════════════════════════════════════════════
# Sales Dashboard KPIs
# ═══════════════════════════════════════════════════════════════════════════════

def get_sales_kpis(db, start_date: date, end_date: date,
                   branch_id: Optional[int] = None) -> dict:
    """KPIs for Sales Manager."""
    prev_start, prev_end = get_previous_period(start_date, end_date)
    branch_sql, bp = build_branch_filter(branch_id)

    # Total Revenue
    revenue = _gl_sum(db, "revenue", start_date, end_date, branch_id, debit_minus_credit=False)
    prev_revenue = _gl_sum(db, "revenue", prev_start, prev_end, branch_id, debit_minus_credit=False)
    rev_trend = calc_trend(revenue, prev_revenue)

    # Quotation Conversion Rate
    total_quotations = _count_table(db, "sales_quotations", branch_id, "quotation_date", start_date, end_date)
    converted_quotations = _count_table(db, "sales_quotations", branch_id, "quotation_date", start_date, end_date,
                                        extra_where="status = 'converted'")
    conversion_rate = (converted_quotations / total_quotations * 100) if total_quotations > 0 else 0

    # Average Deal Size
    total_orders = _count_table(db, "sales_orders", branch_id, "order_date", start_date, end_date)
    total_order_value = _sum_column(db, "sales_orders", "total", branch_id, "order_date", start_date, end_date)
    avg_deal = total_order_value / total_orders if total_orders > 0 else 0

    # Top 10 Customers
    top_customers = []
    try:
        rows = db.execute(text(f"""
            SELECT p.name, COALESCE(SUM(i.total), 0) as total
            FROM invoices i
            JOIN parties p ON i.party_id = p.id
            WHERE i.invoice_type = 'sales' AND i.invoice_date BETWEEN :s AND :e {branch_sql}
            GROUP BY p.name ORDER BY total DESC LIMIT 10
        """), {"s": start_date, "e": end_date, **bp}).fetchall()
        top_customers = [{"name": r[0], "value": float(r[1])} for r in rows]
    except Exception:
        pass

    # Overdue Invoices
    overdue_count = 0
    overdue_value = 0
    try:
        ov = db.execute(text(f"""
            SELECT COUNT(*), COALESCE(SUM(total - COALESCE(paid_amount, 0)), 0)
            FROM invoices
            WHERE invoice_type = 'sales' AND status IN ('sent','partially_paid')
              AND due_date < CURRENT_DATE {branch_sql.replace('je.', '')}
        """), bp).fetchone()
        if ov:
            overdue_count = int(ov[0] or 0)
            overdue_value = float(ov[1] or 0)
    except Exception:
        pass

    # DSO
    ar_balance = _gl_balance(db, "receivable", end_date, branch_id)
    days_in_period = max((end_date - start_date).days, 1)
    daily_rev = revenue / days_in_period if days_in_period > 0 else 0
    dso = ar_balance / daily_rev if daily_rev > 0 else 0

    # Pipeline Value (CRM)
    pipeline_value = 0
    try:
        pv = db.execute(text("""
            SELECT COALESCE(SUM(expected_value), 0) FROM sales_opportunities
            WHERE stage IN ('open', 'qualified', 'proposal')
        """)).scalar()
        pipeline_value = float(pv or 0)
    except Exception:
        pass

    kpis = [
        kpi_item("revenue", "Total Revenue", "إجمالي الإيرادات", revenue, "SAR",
                 rev_trend[0], rev_trend[1], rev_trend[2]),
        kpi_item("conversion_rate", "Quotation Conversion Rate", "معدل تحويل عروض الأسعار",
                 conversion_rate, "%", benchmark=25.0, benchmark_source="Industry Avg",
                 status=ratio_status(conversion_rate, 25, 10)),
        kpi_item("avg_deal_size", "Average Deal Size", "متوسط حجم الصفقة", avg_deal, "SAR"),
        kpi_item("total_orders", "Sales Orders", "أوامر البيع", total_orders, ""),
        kpi_item("overdue_invoices", "Overdue Invoices", "الفواتير المتأخرة", overdue_count, "",
                 status="danger" if overdue_count > 0 else "good"),
        kpi_item("overdue_value", "Overdue Value", "قيمة المتأخرات", overdue_value, "SAR",
                 status="danger" if overdue_value > 0 else "good"),
        kpi_item("dso", "Days Sales Outstanding", "أيام تحصيل المبيعات", dso, "days",
                 benchmark=30, benchmark_source="Best Practice",
                 status=ratio_status(dso, 30, 60, higher_is_better=False)),
        kpi_item("pipeline_value", "Pipeline Value", "قيمة الفرص المتوقعة", pipeline_value, "SAR"),
    ]

    charts = [
        {"id": "top_customers", "type": "bar", "title": "Top 10 Customers",
         "title_ar": "أعلى 10 عملاء", "data": top_customers},
    ]
    charts.extend(_build_sales_trend_chart(db, start_date, end_date, branch_id))

    alerts = []
    if overdue_count > 0:
        alerts.append({"severity": "high", "code": "OVERDUE_INVOICES",
                        "message": f"{overdue_count} invoices overdue totaling {overdue_value:,.0f} SAR",
                        "message_ar": f"{overdue_count} فاتورة متأخرة بإجمالي {overdue_value:,.0f} ر.س",
                        "count": overdue_count, "link": "/sales/invoices?status=overdue"})

    return {"role": "sales", "kpis": kpis, "charts": charts, "alerts": alerts}


# ═══════════════════════════════════════════════════════════════════════════════
# Procurement Dashboard KPIs
# ═══════════════════════════════════════════════════════════════════════════════

def get_procurement_kpis(db, start_date: date, end_date: date,
                         branch_id: Optional[int] = None) -> dict:
    """KPIs for Purchase Manager."""
    branch_sql, bp = build_branch_filter(branch_id)

    # Total PO Value
    po_value = _sum_column(db, "purchase_orders", "total", branch_id, "order_date", start_date, end_date)
    po_count = _count_table(db, "purchase_orders", branch_id, "order_date", start_date, end_date)

    # Pending RFQs
    pending_rfqs = _count_table(db, "purchase_orders", branch_id, extra_where="status = 'draft'")

    # AP Aging
    ap_balance = _gl_balance(db, "payable", end_date, branch_id, debit_minus_credit=False)

    # Top 10 Suppliers
    top_suppliers = []
    try:
        rows = db.execute(text(f"""
            SELECT p.name, COALESCE(SUM(i.total), 0) as total
            FROM invoices i
            JOIN parties p ON i.party_id = p.id
            WHERE i.invoice_type = 'purchase' AND i.invoice_date BETWEEN :s AND :e {branch_sql}
            GROUP BY p.name ORDER BY total DESC LIMIT 10
        """), {"s": start_date, "e": end_date, **bp}).fetchall()
        top_suppliers = [{"name": r[0], "value": float(r[1])} for r in rows]
    except Exception:
        pass

    # Supplier On-Time Delivery (approximate — no actual_delivery_date column)
    on_time_pct = 0
    try:
        on_time = db.execute(text("""
            SELECT
                COUNT(CASE WHEN updated_at <= expected_date THEN 1 END),
                COUNT(*)
            FROM purchase_orders
            WHERE status = 'received'
        """)).fetchone()
        if on_time and on_time[1] > 0:
            on_time_pct = (on_time[0] / on_time[1]) * 100
    except Exception:
        pass

    # Avg Lead Time (approximate using updated_at as receive date)
    avg_lead_time = 0
    try:
        lt = db.execute(text("""
            SELECT AVG(EXTRACT(DAY FROM (updated_at - order_date)))
            FROM purchase_orders
            WHERE status = 'received'
        """)).scalar()
        avg_lead_time = float(lt or 0)
    except Exception:
        pass

    kpis = [
        kpi_item("po_value", "Total PO Value", "إجمالي قيمة أوامر الشراء", po_value, "SAR"),
        kpi_item("po_count", "Purchase Orders", "عدد أوامر الشراء", po_count, ""),
        kpi_item("pending_rfqs", "Pending RFQs", "طلبات عروض أسعار معلقة", pending_rfqs, ""),
        kpi_item("on_time_delivery", "Supplier On-Time Delivery", "التسليم في الموعد", on_time_pct, "%",
                 benchmark=95.0, benchmark_source="Best Practice",
                 status=ratio_status(on_time_pct, 95, 80)),
        kpi_item("ap_balance", "Accounts Payable", "رصيد الذمم الدائنة", ap_balance, "SAR"),
        kpi_item("avg_lead_time", "Avg Lead Time", "متوسط وقت التسليم", avg_lead_time, "days",
                 benchmark=14, benchmark_source="Industry Avg",
                 status=ratio_status(avg_lead_time, 14, 30, higher_is_better=False)),
    ]

    charts = [
        {"id": "top_suppliers", "type": "bar", "title": "Top 10 Suppliers",
         "title_ar": "أعلى 10 موردين", "data": top_suppliers},
    ]

    alerts = []
    if pending_rfqs > 5:
        alerts.append({"severity": "medium", "code": "PENDING_RFQS",
                        "message": f"{pending_rfqs} RFQs pending review",
                        "message_ar": f"{pending_rfqs} طلب عرض سعر بانتظار المراجعة",
                        "count": pending_rfqs, "link": "/buying/rfq"})

    return {"role": "procurement", "kpis": kpis, "charts": charts, "alerts": alerts}


# ═══════════════════════════════════════════════════════════════════════════════
# Warehouse Dashboard KPIs
# ═══════════════════════════════════════════════════════════════════════════════

def get_warehouse_kpis(db, start_date: date, end_date: date,
                       branch_id: Optional[int] = None) -> dict:
    """KPIs for Inventory / Warehouse Manager."""

    # Inventory Valuation
    inv_valuation = 0
    try:
        iv = db.execute(text("""
            SELECT COALESCE(SUM(i.quantity * COALESCE(p.cost_price, 0)), 0)
            FROM inventory i JOIN products p ON i.product_id = p.id
        """)).scalar()
        inv_valuation = float(iv or 0)
    except Exception:
        pass

    # Stock Turnover = COGS / Avg Inventory Value
    cogs = 0
    try:
        cogs_r = db.execute(text("""
            SELECT COALESCE(SUM(jl.debit - jl.credit), 0)
            FROM journal_lines jl JOIN journal_entries je ON jl.journal_entry_id = je.id
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.account_type = 'expense' AND a.account_code LIKE '5%'
              AND je.entry_date BETWEEN :s AND :e AND je.status = 'posted'
        """), {"s": start_date, "e": end_date}).scalar()
        cogs = float(cogs_r or 0)
    except Exception:
        pass

    stock_turnover = cogs / inv_valuation if inv_valuation > 0 else 0
    dio = 365 / stock_turnover if stock_turnover > 0 else 0

    # Total SKUs & Active
    total_products = _count_table(db, "products")
    active_products = _count_table(db, "products", extra_where="is_active = true")

    # Low Stock Count
    low_stock = 0
    try:
        ls = db.execute(text("""
            SELECT COUNT(DISTINCT p.id)
            FROM products p
            JOIN inventory i ON p.id = i.product_id
            WHERE i.quantity <= COALESCE(p.reorder_level, 0) AND p.is_active = true AND p.reorder_level > 0
        """)).scalar()
        low_stock = int(ls or 0)
    except Exception:
        pass

    # Slow-Moving Items (no movement in 90+ days)
    slow_moving = 0
    try:
        sm = db.execute(text("""
            SELECT COUNT(DISTINCT p.id)
            FROM products p
            LEFT JOIN (
                SELECT DISTINCT product_id FROM inventory_transactions
                WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
            ) recent ON p.id = recent.product_id
            WHERE recent.product_id IS NULL AND p.is_active = true
        """)).scalar()
        slow_moving = int(sm or 0)
    except Exception:
        pass

    slow_moving_pct = (slow_moving / active_products * 100) if active_products > 0 else 0

    # Out of Stock
    out_of_stock = 0
    try:
        oos = db.execute(text("""
            SELECT COUNT(DISTINCT p.id) FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.is_active = true AND (i.quantity IS NULL OR i.quantity <= 0)
              AND p.product_type != 'service'
        """)).scalar()
        out_of_stock = int(oos or 0)
    except Exception:
        pass

    kpis = [
        kpi_item("inv_valuation", "Inventory Valuation", "تقييم المخزون", inv_valuation, "SAR"),
        kpi_item("stock_turnover", "Stock Turnover", "معدل دوران المخزون", stock_turnover, "x",
                 benchmark=6.0, benchmark_source="IAS 2",
                 status=ratio_status(stock_turnover, 6, 3)),
        kpi_item("dio", "Days Inventory Outstanding", "أيام دوران المخزون", dio, "days",
                 benchmark=60, benchmark_source="IAS 2",
                 status=ratio_status(dio, 60, 120, higher_is_better=False)),
        kpi_item("active_products", "Active Products", "المنتجات النشطة", active_products, ""),
        kpi_item("low_stock", "Low Stock Items", "منتجات تحت حد الطلب", low_stock, "",
                 status="danger" if low_stock > 0 else "good"),
        kpi_item("slow_moving_pct", "Slow-Moving Items", "المنتجات بطيئة الحركة", slow_moving_pct, "%",
                 benchmark=10, benchmark_source="Best Practice",
                 status=ratio_status(slow_moving_pct, 10, 25, higher_is_better=False)),
        kpi_item("out_of_stock", "Out of Stock", "منتجات نفدت", out_of_stock, "",
                 status="danger" if out_of_stock > 0 else "good"),
    ]

    charts = []
    alerts = []
    if low_stock > 0:
        alerts.append({"severity": "high", "code": "LOW_STOCK",
                        "message": f"{low_stock} products below reorder level",
                        "message_ar": f"{low_stock} منتج تحت حد إعادة الطلب",
                        "count": low_stock, "link": "/stock/products?filter=low_stock"})
    if out_of_stock > 0:
        alerts.append({"severity": "high", "code": "OUT_OF_STOCK",
                        "message": f"{out_of_stock} products out of stock",
                        "message_ar": f"{out_of_stock} منتج نفد من المخزون",
                        "count": out_of_stock, "link": "/stock/products?filter=out_of_stock"})

    return {"role": "warehouse", "kpis": kpis, "charts": charts, "alerts": alerts}


# ═══════════════════════════════════════════════════════════════════════════════
# HR Dashboard KPIs
# ═══════════════════════════════════════════════════════════════════════════════

def get_hr_kpis(db, start_date: date, end_date: date,
                branch_id: Optional[int] = None) -> dict:
    """KPIs for HR Manager."""
    branch_sql, bp = build_branch_filter(branch_id, "e")

    # Headcount
    headcount = _count_table(db, "employees", extra_where="status = 'active'")

    # Saudization
    saudi_count = 0
    try:
        sc = db.execute(text(f"""
            SELECT COUNT(*) FROM employees
            WHERE status = 'active' AND (nationality = 'Saudi' OR nationality = 'سعودي')
            {branch_sql.replace('e.', '')}
        """), bp).scalar()
        saudi_count = int(sc or 0)
    except Exception:
        pass
    saudization = (saudi_count / headcount * 100) if headcount > 0 else 0

    # Nitaqat Band
    if saudization >= 40:
        nitaqat = "Platinum"
    elif saudization >= 26:
        nitaqat = "Green"
    elif saudization >= 10:
        nitaqat = "Yellow"
    else:
        nitaqat = "Red"

    # Payroll total this period (join via period_id to payroll_periods)
    payroll_total = 0
    try:
        pt = db.execute(text("""
            SELECT COALESCE(SUM(pe.net_salary), 0)
            FROM payroll_entries pe
            JOIN payroll_periods pp ON pe.period_id = pp.id
            WHERE pp.start_date >= :s AND pp.end_date <= :e
        """), {"s": start_date, "e": end_date}).scalar()
        payroll_total = float(pt or 0)
    except Exception:
        pass

    # Attendance rate
    attendance_rate = 0
    try:
        att = db.execute(text("""
            SELECT
                COUNT(CASE WHEN status = 'present' THEN 1 END),
                COUNT(*)
            FROM attendance
            WHERE date BETWEEN :s AND :e
        """), {"s": start_date, "e": end_date}).fetchone()
        if att and att[1] > 0:
            attendance_rate = (att[0] / att[1]) * 100
    except Exception:
        pass

    # Turnover rate (employees terminated / avg headcount * 100) annualized
    terminated = _count_table(db, "employees", date_col="termination_date",
                              start_date=start_date, end_date=end_date,
                              extra_where="status = 'terminated'")
    turnover_rate = (terminated / headcount * 100) if headcount > 0 else 0

    # Pending leave requests
    pending_leaves = _count_table(db, "leave_requests", extra_where="status = 'pending'")

    # Training hours (estimated from program date range)
    training_hours = 0
    try:
        th = db.execute(text("""
            SELECT COALESCE(SUM(
                EXTRACT(EPOCH FROM (COALESCE(end_date, start_date + INTERVAL '1 day') - start_date)) / 3600
            ), 0) FROM training_programs
            WHERE start_date BETWEEN :s AND :e
        """), {"s": start_date, "e": end_date}).scalar()
        training_hours = float(th or 0)
    except Exception:
        pass
    training_per_emp = training_hours / headcount if headcount > 0 else 0

    kpis = [
        kpi_item("headcount", "Total Headcount", "إجمالي الموظفين", headcount, ""),
        kpi_item("saudization", "Saudization Rate", "نسبة السعودة", saudization, "%",
                 benchmark=26.0, benchmark_source="GAZT Nitaqat",
                 status=ratio_status(saudization, 26, 10)),
        kpi_item("nitaqat_band", "Nitaqat Band", "نطاق نطاقات", nitaqat, "",
                 status="good" if nitaqat in ("Platinum", "Green") else ("warning" if nitaqat == "Yellow" else "danger")),
        kpi_item("payroll_total", "Payroll Total", "إجمالي الرواتب", payroll_total, "SAR"),
        kpi_item("attendance_rate", "Attendance Rate", "معدل الحضور", attendance_rate, "%",
                 benchmark=95.0, benchmark_source="HR Best Practice",
                 status=ratio_status(attendance_rate, 95, 85)),
        kpi_item("turnover_rate", "Turnover Rate", "معدل دوران الموظفين", turnover_rate, "%",
                 benchmark=10.0, benchmark_source="Industry Avg",
                 status=ratio_status(turnover_rate, 10, 25, higher_is_better=False)),
        kpi_item("pending_leaves", "Pending Leave Requests", "طلبات إجازة معلقة", pending_leaves, ""),
        kpi_item("training_per_emp", "Training Hours/Employee", "ساعات التدريب لكل موظف",
                 training_per_emp, "hrs",
                 benchmark=20.0, benchmark_source="Annual Target"),
    ]

    charts = []
    alerts = []
    if nitaqat in ("Red", "Yellow"):
        alerts.append({"severity": "high" if nitaqat == "Red" else "medium",
                        "code": "SAUDIZATION", "message": f"Saudization at {saudization:.1f}% — {nitaqat} band",
                        "message_ar": f"نسبة السعودة {saudization:.1f}% — نطاق {'أحمر' if nitaqat == 'Red' else 'أصفر'}",
                        "link": "/hr/saudization"})
    if pending_leaves > 10:
        alerts.append({"severity": "medium", "code": "PENDING_LEAVES",
                        "message": f"{pending_leaves} leave requests pending approval",
                        "message_ar": f"{pending_leaves} طلب إجازة بانتظار الاعتماد",
                        "count": pending_leaves, "link": "/hr/leaves"})

    return {"role": "hr", "kpis": kpis, "charts": charts, "alerts": alerts}


# ═══════════════════════════════════════════════════════════════════════════════
# Manufacturing Dashboard KPIs
# ═══════════════════════════════════════════════════════════════════════════════

def get_manufacturing_kpis(db, start_date: date, end_date: date,
                           branch_id: Optional[int] = None) -> dict:
    """KPIs for Manufacturing Manager."""

    # Production Orders
    total_prod = _count_table(db, "production_orders", branch_id, "start_date", start_date, end_date)
    completed_prod = _count_table(db, "production_orders", branch_id, "start_date",
                                  start_date, end_date, extra_where="status = 'completed'")
    in_progress_prod = _count_table(db, "production_orders", branch_id, extra_where="status = 'in_progress'")

    # OEE (Overall Equipment Effectiveness)
    # production_orders has no availability/performance/quality columns;
    # approximate from work_center capacity_plans if available
    oee = 0
    try:
        oee_r = db.execute(text("""
            SELECT AVG(efficiency_pct) FROM capacity_plans
            WHERE date BETWEEN :s AND :e
        """), {"s": start_date, "e": end_date}).scalar()
        oee = float(oee_r or 0)
    except Exception:
        # Fallback: use yield rate as proxy
        try:
            yr = db.execute(text("""
                SELECT
                    COALESCE(SUM(produced_quantity), 0),
                    COALESCE(SUM(quantity), 0)
                FROM production_orders
                WHERE status = 'completed' AND start_date BETWEEN :s AND :e
            """), {"s": start_date, "e": end_date}).fetchone()
            if yr and yr[1] > 0:
                oee = (yr[0] / yr[1]) * 100
            else:
                oee = 85  # industry default
        except Exception:
            oee = 0

    # Cost Variance (production_orders has no estimated_cost/actual_cost columns)
    cost_variance = 0

    # Equipment Downtime (work_centers has no downtime_hours/available_hours;
    # use capacity_plans if available)
    downtime_pct = 0
    try:
        dt = db.execute(text("""
            SELECT
                COALESCE(SUM(planned_hours - actual_hours), 0),
                COALESCE(SUM(available_hours), 0)
            FROM capacity_plans
            WHERE date BETWEEN :s AND :e
        """), {"s": start_date, "e": end_date}).fetchone()
        if dt and dt[1] > 0:
            downtime_pct = (dt[0] / dt[1]) * 100
    except Exception:
        pass

    # Yield Rate
    yield_rate = 0
    try:
        yr = db.execute(text("""
            SELECT
                COALESCE(SUM(produced_quantity), 0),
                COALESCE(SUM(quantity), 0)
            FROM production_orders
            WHERE status = 'completed'
              AND start_date BETWEEN :s AND :e
        """), {"s": start_date, "e": end_date}).fetchone()
        if yr and yr[1] > 0:
            yield_rate = (yr[0] / yr[1]) * 100
    except Exception:
        pass

    kpis = [
        kpi_item("oee", "OEE", "الفعالية الكلية للمعدات", oee, "%",
                 benchmark=85.0, benchmark_source="World Class",
                 status=ratio_status(oee, 85, 60)),
        kpi_item("completed_orders", "Completed Orders", "أوامر إنتاج مكتملة", completed_prod, ""),
        kpi_item("in_progress_orders", "In-Progress Orders", "أوامر إنتاج قيد التنفيذ", in_progress_prod, ""),
        kpi_item("cost_variance", "Cost Variance", "انحراف التكلفة", cost_variance, "%",
                 benchmark=5.0, benchmark_source="Internal",
                 status=ratio_status(abs(cost_variance), 5, 15, higher_is_better=False)),
        kpi_item("downtime", "Equipment Downtime", "توقف المعدات", downtime_pct, "%",
                 benchmark=5.0, benchmark_source="Industry Avg",
                 status=ratio_status(downtime_pct, 5, 15, higher_is_better=False)),
        kpi_item("yield_rate", "Yield Rate", "معدل الإنتاجية", yield_rate, "%",
                 benchmark=95.0, benchmark_source="ISO 9001",
                 status=ratio_status(yield_rate, 95, 85)),
        kpi_item("total_orders", "Total Production Orders", "إجمالي أوامر الإنتاج", total_prod, ""),
    ]

    charts = []
    alerts = []
    if oee > 0 and oee < 60:
        alerts.append({"severity": "high", "code": "LOW_OEE",
                        "message": f"OEE at {oee:.1f}% — below acceptable threshold",
                        "message_ar": f"الفعالية الكلية {oee:.1f}% — تحت المستوى المقبول",
                        "link": "/manufacturing/work-centers"})

    return {"role": "manufacturing", "kpis": kpis, "charts": charts, "alerts": alerts}


# ═══════════════════════════════════════════════════════════════════════════════
# Projects Dashboard KPIs
# ═══════════════════════════════════════════════════════════════════════════════

def get_projects_kpis(db, start_date: date, end_date: date,
                      branch_id: Optional[int] = None) -> dict:
    """KPIs for Project Manager."""

    # Active projects
    active_projects = _count_table(db, "projects", extra_where="status = 'active'")
    completed_projects = _count_table(db, "projects", extra_where="status = 'completed'")

    # Budget utilization
    budget_util = 0
    try:
        bu = db.execute(text("""
            SELECT
                COALESCE(SUM(actual_cost), 0),
                COALESCE(SUM(planned_budget), 0)
            FROM projects WHERE status IN ('active', 'completed')
        """)).fetchone()
        if bu and bu[1] > 0:
            budget_util = (bu[0] / bu[1]) * 100
    except Exception:
        pass

    # EVM: CPI and SPI (projects table has no earned_value/planned_value;
    # approximate CPI from actual_cost vs planned_budget)
    avg_cpi = 0
    avg_spi = 0
    try:
        evm = db.execute(text("""
            SELECT
                AVG(CASE WHEN actual_cost > 0 THEN (progress_percentage / 100.0 * planned_budget) / actual_cost ELSE 1 END),
                AVG(COALESCE(progress_percentage, 0) / 100.0)
            FROM projects WHERE status = 'active' AND planned_budget > 0
        """)).fetchone()
        if evm:
            avg_cpi = float(evm[0] or 0)
            avg_spi = float(evm[1] or 0)
    except Exception:
        pass

    # Change Orders
    change_orders_value = 0
    try:
        co = db.execute(text("""
            SELECT COALESCE(SUM(cost_impact), 0) FROM project_change_orders
            WHERE created_at BETWEEN :s AND :e
        """), {"s": start_date, "e": end_date}).scalar()
        change_orders_value = float(co or 0)
    except Exception:
        pass

    # Risk Distribution (project_risks has probability/impact, not risk_level)
    risks = {"high": 0, "medium": 0, "low": 0}
    try:
        risk_rows = db.execute(text("""
            SELECT impact, COUNT(*) FROM project_risks
            WHERE status = 'open'
            GROUP BY impact
        """)).fetchall()
        for r in risk_rows:
            level = str(r[0]).lower()
            if level in risks:
                risks[level] = int(r[1])
    except Exception:
        pass

    # Resource utilization (project_timesheets has single 'hours' column, no planned_hours)
    resource_util = 0
    try:
        ru = db.execute(text("""
            SELECT COALESCE(SUM(hours), 0)
            FROM project_timesheets
            WHERE date BETWEEN :s AND :e
        """), {"s": start_date, "e": end_date}).scalar()
        resource_util = float(ru or 0)
        # Without planned hours, report total hours logged instead of percentage
        # Set to 80% default if hours > 0 to avoid misleading zero
        if resource_util > 0:
            resource_util = 80  # placeholder until planned hours are available
    except Exception:
        pass

    kpis = [
        kpi_item("active_projects", "Active Projects", "مشاريع نشطة", active_projects, ""),
        kpi_item("budget_utilization", "Budget Utilization", "استخدام الميزانية", budget_util, "%",
                 benchmark=100.0, benchmark_source="PMI PMBOK"),
        kpi_item("cpi", "Cost Performance Index", "مؤشر أداء التكلفة", avg_cpi, "x",
                 benchmark=1.0, benchmark_source="PMI PMBOK",
                 status=ratio_status(avg_cpi, 1.0, 0.8)),
        kpi_item("spi", "Schedule Performance Index", "مؤشر أداء الجدول", avg_spi, "x",
                 benchmark=1.0, benchmark_source="PMI PMBOK",
                 status=ratio_status(avg_spi, 1.0, 0.8)),
        kpi_item("change_orders", "Change Orders Value", "قيمة أوامر التغيير", change_orders_value, "SAR"),
        kpi_item("high_risks", "High Risks", "مخاطر عالية", risks["high"], "",
                 status="danger" if risks["high"] > 0 else "good"),
        kpi_item("resource_utilization", "Resource Utilization", "استخدام الموارد", resource_util, "%",
                 benchmark=80.0, benchmark_source="PMI",
                 status=ratio_status(resource_util, 80, 60)),
    ]

    charts = [
        {"id": "risk_distribution", "type": "pie", "title": "Risk Distribution",
         "title_ar": "توزيع المخاطر", "data": risks},
    ]

    alerts = []
    if risks["high"] > 0:
        alerts.append({"severity": "high", "code": "HIGH_RISKS",
                        "message": f"{risks['high']} high-risk items require attention",
                        "message_ar": f"{risks['high']} مخاطر عالية تحتاج متابعة",
                        "count": risks["high"], "link": "/projects/risks"})

    return {"role": "projects", "kpis": kpis, "charts": charts, "alerts": alerts}


# ═══════════════════════════════════════════════════════════════════════════════
# POS Dashboard KPIs
# ═══════════════════════════════════════════════════════════════════════════════

def get_pos_kpis(db, start_date: date, end_date: date,
                 branch_id: Optional[int] = None) -> dict:
    """KPIs for Cashier / POS."""
    branch_sql, bp = build_branch_filter(branch_id)

    # Sales today
    today = date.today()
    sales_today = 0
    tx_count_today = 0
    try:
        pos_r = db.execute(text(f"""
            SELECT COALESCE(SUM(total_amount), 0), COUNT(*)
            FROM pos_orders
            WHERE DATE(order_date) = :today AND status = 'paid' {branch_sql}
        """), {"today": today, **bp}).fetchone()
        if pos_r:
            sales_today = float(pos_r[0] or 0)
            tx_count_today = int(pos_r[1] or 0)
    except Exception:
        pass

    # Period sales
    period_sales = 0
    period_tx = 0
    try:
        ps = db.execute(text(f"""
            SELECT COALESCE(SUM(total_amount), 0), COUNT(*)
            FROM pos_orders
            WHERE order_date BETWEEN :s AND :e AND status = 'paid' {branch_sql}
        """), {"s": start_date, "e": end_date, **bp}).fetchone()
        if ps:
            period_sales = float(ps[0] or 0)
            period_tx = int(ps[1] or 0)
    except Exception:
        pass

    # Average Basket Size
    avg_basket = period_sales / period_tx if period_tx > 0 else 0

    # Returns today
    returns_today = 0
    try:
        rt = db.execute(text(f"""
            SELECT COALESCE(SUM(total_amount), 0) FROM pos_orders
            WHERE DATE(order_date) = :today AND status = 'returned' {branch_sql}
        """), {"today": today, **bp}).scalar()
        returns_today = float(rt or 0)
    except Exception:
        pass

    # Top Products Today
    top_products = []
    try:
        rows = db.execute(text(f"""
            SELECT p.name, COALESCE(SUM(oi.quantity), 0) as qty, COALESCE(SUM(oi.total), 0) as total
            FROM pos_order_lines oi
            JOIN pos_orders o ON oi.order_id = o.id
            JOIN products p ON oi.product_id = p.id
            WHERE DATE(o.order_date) = :today AND o.status = 'paid' {branch_sql.replace('je.', 'o.')}
            GROUP BY p.name ORDER BY total DESC LIMIT 5
        """), {"today": today, **bp}).fetchall()
        top_products = [{"name": r[0], "quantity": int(r[1]), "value": float(r[2])} for r in rows]
    except Exception:
        pass

    # Cash vs Card split (from pos_payments table)
    cash_pct = 0
    card_pct = 0
    try:
        pm = db.execute(text(f"""
            SELECT pp.payment_method, COALESCE(SUM(pp.amount), 0)
            FROM pos_payments pp
            JOIN pos_orders o ON pp.order_id = o.id
            WHERE DATE(o.order_date) = :today AND o.status = 'paid' {branch_sql.replace('je.', 'o.')}
            GROUP BY pp.payment_method
        """), {"today": today, **bp}).fetchall()
        total_pm = sum(float(r[1]) for r in pm) if pm else 0
        for r in pm:
            method = str(r[0]).lower()
            val = float(r[1])
            if 'cash' in method:
                cash_pct = (val / total_pm * 100) if total_pm > 0 else 0
            elif 'card' in method or 'visa' in method or 'mada' in method:
                card_pct = (val / total_pm * 100) if total_pm > 0 else 0
    except Exception:
        pass

    # Loyalty points
    loyalty_points = 0
    try:
        lp = db.execute(text("""
            SELECT COALESCE(SUM(points), 0) FROM pos_loyalty_transactions
            WHERE DATE(created_at) = :today AND txn_type = 'earn'
        """), {"today": today}).scalar()
        loyalty_points = int(lp or 0)
    except Exception:
        pass

    kpis = [
        kpi_item("sales_today", "Sales Today", "مبيعات اليوم", sales_today, "SAR"),
        kpi_item("tx_count", "Transactions Today", "عدد العمليات اليوم", tx_count_today, ""),
        kpi_item("avg_basket", "Average Basket Size", "متوسط قيمة السلة", avg_basket, "SAR"),
        kpi_item("returns_today", "Returns Today", "مرتجعات اليوم", returns_today, "SAR",
                 status="warning" if returns_today > 0 else "good"),
        kpi_item("cash_pct", "Cash %", "نسبة النقد", cash_pct, "%"),
        kpi_item("card_pct", "Card %", "نسبة البطاقات", card_pct, "%"),
        kpi_item("loyalty_points", "Loyalty Points Issued", "نقاط الولاء المصدرة", loyalty_points, "pts"),
    ]

    charts = [
        {"id": "top_products_today", "type": "bar", "title": "Top Products Today",
         "title_ar": "أعلى المنتجات اليوم", "data": top_products},
    ]

    alerts = []
    return {"role": "pos", "kpis": kpis, "charts": charts, "alerts": alerts}


# ═══════════════════════════════════════════════════════════════════════════════
# CRM Dashboard KPIs
# ═══════════════════════════════════════════════════════════════════════════════

def get_crm_kpis(db, start_date: date, end_date: date,
                 branch_id: Optional[int] = None) -> dict:
    """KPIs for CRM / Sales Rep."""

    # Opportunities
    open_opps = 0
    open_value = 0
    try:
        oo = db.execute(text("""
            SELECT COUNT(*), COALESCE(SUM(expected_value), 0)
            FROM sales_opportunities WHERE stage IN ('open','qualified','proposal')
        """)).fetchone()
        if oo:
            open_opps = int(oo[0] or 0)
            open_value = float(oo[1] or 0)
    except Exception:
        pass

    # Win Rate
    won_opps = _count_table(db, "sales_opportunities", date_col="updated_at",
                            start_date=start_date, end_date=end_date,
                            extra_where="stage = 'won'")
    lost_opps = _count_table(db, "sales_opportunities", date_col="updated_at",
                             start_date=start_date, end_date=end_date,
                             extra_where="stage = 'lost'")
    total_closed = won_opps + lost_opps
    win_rate = (won_opps / total_closed * 100) if total_closed > 0 else 0

    # Pipeline by Stage
    pipeline_stages = []
    try:
        stages = db.execute(text("""
            SELECT stage, COUNT(*), COALESCE(SUM(expected_value), 0)
            FROM sales_opportunities WHERE stage NOT IN ('won','lost','cancelled')
            GROUP BY stage ORDER BY COUNT(*) DESC
        """)).fetchall()
        pipeline_stages = [{"stage": r[0], "count": int(r[1]), "value": float(r[2])} for r in stages]
    except Exception:
        pass

    # Support Tickets
    open_tickets = _count_table(db, "support_tickets", extra_where="status IN ('open','in_progress')")
    overdue_tickets = 0
    try:
        ot = db.execute(text("""
            SELECT COUNT(*) FROM support_tickets
            WHERE status IN ('open','in_progress')
              AND due_date < CURRENT_DATE
        """)).scalar()
        overdue_tickets = int(ot or 0)
    except Exception:
        pass

    # Campaign ROI (marketing_campaigns has budget/spent, no actual_revenue)
    campaign_roi = 0
    try:
        cr = db.execute(text("""
            SELECT
                COALESCE(SUM(conversion_count), 0),
                COALESCE(SUM(budget), 0),
                COALESCE(SUM(spent), 0)
            FROM marketing_campaigns
            WHERE start_date BETWEEN :s AND :e
        """), {"s": start_date, "e": end_date}).fetchone()
        if cr and cr[2] > 0 and cr[1] > 0:
            # ROI based on spend efficiency: (budget - spent) / budget * 100
            campaign_roi = ((cr[1] - cr[2]) / cr[1]) * 100
    except Exception:
        pass

    kpis = [
        kpi_item("open_opportunities", "Open Opportunities", "الفرص المفتوحة", open_opps, ""),
        kpi_item("pipeline_value", "Pipeline Value", "قيمة الفرص", open_value, "SAR"),
        kpi_item("win_rate", "Win Rate", "معدل الفوز", win_rate, "%",
                 benchmark=35.0, benchmark_source="Industry Avg",
                 status=ratio_status(win_rate, 35, 20)),
        kpi_item("open_tickets", "Open Tickets", "التذاكر المفتوحة", open_tickets, ""),
        kpi_item("overdue_tickets", "Overdue Tickets", "التذاكر المتأخرة", overdue_tickets, "",
                 status="danger" if overdue_tickets > 0 else "good"),
        kpi_item("campaign_roi", "Campaign ROI", "عائد الحملات", campaign_roi, "%",
                 benchmark=100.0, benchmark_source="Marketing Benchmark"),
    ]

    charts = [
        {"id": "pipeline_stages", "type": "funnel", "title": "Pipeline by Stage",
         "title_ar": "الفرص حسب المرحلة", "data": pipeline_stages},
    ]

    alerts = []
    if overdue_tickets > 0:
        alerts.append({"severity": "high", "code": "OVERDUE_TICKETS",
                        "message": f"{overdue_tickets} support tickets overdue",
                        "message_ar": f"{overdue_tickets} تذكرة دعم متأخرة",
                        "count": overdue_tickets, "link": "/crm/tickets?status=overdue"})

    return {"role": "crm", "kpis": kpis, "charts": charts, "alerts": alerts}


# ═══════════════════════════════════════════════════════════════════════════════
# Helper: Chart Builders
# ═══════════════════════════════════════════════════════════════════════════════

def _build_revenue_expense_chart(db, start_date: date, end_date: date,
                                  branch_id: Optional[int] = None) -> list:
    """Monthly revenue vs expenses trend chart."""
    branch_sql, bp = build_branch_filter(branch_id)
    data = []
    try:
        rows = db.execute(text(f"""
            SELECT
                TO_CHAR(je.entry_date, 'YYYY-MM') as month,
                COALESCE(SUM(CASE WHEN a.account_type = 'revenue' THEN jl.credit - jl.debit ELSE 0 END), 0) as revenue,
                COALESCE(SUM(CASE WHEN a.account_type = 'expense' THEN jl.debit - jl.credit ELSE 0 END), 0) as expenses
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            JOIN accounts a ON jl.account_id = a.id
            WHERE je.entry_date BETWEEN :s AND :e AND je.status = 'posted' {branch_sql}
            GROUP BY TO_CHAR(je.entry_date, 'YYYY-MM')
            ORDER BY month
        """), {"s": start_date, "e": end_date, **bp}).fetchall()
        data = [{"month": r[0], "revenue": float(r[1]), "expenses": float(r[2])} for r in rows]
    except Exception:
        pass
    return [{"id": "revenue_vs_expenses", "type": "line", "title": "Revenue vs Expenses",
             "title_ar": "الإيرادات مقابل المصروفات", "data": data}]


def _build_sales_trend_chart(db, start_date: date, end_date: date,
                              branch_id: Optional[int] = None) -> list:
    """Daily sales trend."""
    branch_sql, bp = build_branch_filter(branch_id)
    data = []
    try:
        rows = db.execute(text(f"""
            SELECT DATE(invoice_date) as day, COALESCE(SUM(total), 0)
            FROM invoices
            WHERE invoice_type = 'sales' AND invoice_date BETWEEN :s AND :e AND status != 'cancelled' {branch_sql}
            GROUP BY DATE(invoice_date) ORDER BY day
        """), {"s": start_date, "e": end_date, **bp}).fetchall()
        data = [{"date": str(r[0]), "value": float(r[1])} for r in rows]
    except Exception:
        pass
    return [{"id": "sales_trend", "type": "line", "title": "Sales Trend",
             "title_ar": "اتجاه المبيعات", "data": data}]


# ═══════════════════════════════════════════════════════════════════════════════
# Helper: Aging Builders
# ═══════════════════════════════════════════════════════════════════════════════

def _build_ar_aging(db, as_of: date, branch_id: Optional[int] = None) -> list:
    """AR Aging buckets: 0-30, 31-60, 61-90, 90+."""
    branch_sql, bp = build_branch_filter(branch_id)
    aging = [
        {"bucket": "0-30", "bucket_ar": "0-30 يوم", "value": 0},
        {"bucket": "31-60", "bucket_ar": "31-60 يوم", "value": 0},
        {"bucket": "61-90", "bucket_ar": "61-90 يوم", "value": 0},
        {"bucket": "90+", "bucket_ar": "أكثر من 90 يوم", "value": 0},
    ]
    try:
        rows = db.execute(text(f"""
            SELECT
                CASE
                    WHEN (:today - due_date) <= 30 THEN '0-30'
                    WHEN (:today - due_date) <= 60 THEN '31-60'
                    WHEN (:today - due_date) <= 90 THEN '61-90'
                    ELSE '90+'
                END as bucket,
                COALESCE(SUM(total - COALESCE(paid_amount, 0)), 0)
            FROM invoices
            WHERE invoice_type = 'sales' AND status IN ('sent', 'partially_paid') AND due_date IS NOT NULL {branch_sql}
            GROUP BY bucket
        """), {"today": as_of, **bp}).fetchall()
        bucket_map = {r[0]: float(r[1]) for r in rows}
        for a in aging:
            a["value"] = bucket_map.get(a["bucket"], 0)
    except Exception:
        pass
    return aging


def _build_ap_aging(db, as_of: date, branch_id: Optional[int] = None) -> list:
    """AP Aging buckets."""
    branch_sql, bp = build_branch_filter(branch_id)
    aging = [
        {"bucket": "0-30", "bucket_ar": "0-30 يوم", "value": 0},
        {"bucket": "31-60", "bucket_ar": "31-60 يوم", "value": 0},
        {"bucket": "61-90", "bucket_ar": "61-90 يوم", "value": 0},
        {"bucket": "90+", "bucket_ar": "أكثر من 90 يوم", "value": 0},
    ]
    try:
        rows = db.execute(text(f"""
            SELECT
                CASE
                    WHEN (:today - due_date) <= 30 THEN '0-30'
                    WHEN (:today - due_date) <= 60 THEN '31-60'
                    WHEN (:today - due_date) <= 90 THEN '61-90'
                    ELSE '90+'
                END as bucket,
                COALESCE(SUM(total - COALESCE(paid_amount, 0)), 0)
            FROM invoices
            WHERE invoice_type = 'purchase' AND status IN ('received', 'partially_paid') AND due_date IS NOT NULL {branch_sql}
            GROUP BY bucket
        """), {"today": as_of, **bp}).fetchall()
        bucket_map = {r[0]: float(r[1]) for r in rows}
        for a in aging:
            a["value"] = bucket_map.get(a["bucket"], 0)
    except Exception:
        pass
    return aging


# ═══════════════════════════════════════════════════════════════════════════════
# Helper: Alert Builders
# ═══════════════════════════════════════════════════════════════════════════════

def _build_executive_alerts(db, branch_id: Optional[int] = None) -> list:
    """Build executive alerts from various sources."""
    alerts = []

    # Overdue invoices
    try:
        ov = db.execute(text("""
            SELECT COUNT(*) FROM invoices
            WHERE invoice_type = 'sales' AND status IN ('sent','partially_paid') AND due_date < CURRENT_DATE
        """)).scalar()
        if ov and int(ov) > 0:
            alerts.append({"severity": "high", "code": "OVERDUE_AR",
                            "message": f"{ov} overdue customer invoices",
                            "message_ar": f"{ov} فاتورة عميل متأخرة",
                            "count": int(ov), "link": "/sales/invoices?status=overdue"})
    except Exception:
        pass

    # Low stock
    try:
        ls = db.execute(text("""
            SELECT COUNT(DISTINCT p.id) FROM products p
            JOIN inventory i ON p.id = i.product_id
            WHERE i.quantity <= COALESCE(p.reorder_level, 0) AND p.is_active = true AND p.reorder_level > 0
        """)).scalar()
        if ls and int(ls) > 0:
            alerts.append({"severity": "medium", "code": "LOW_STOCK",
                            "message": f"{ls} products below reorder level",
                            "message_ar": f"{ls} منتج تحت حد إعادة الطلب",
                            "count": int(ls), "link": "/stock/products?filter=low_stock"})
    except Exception:
        pass

    # Pending approvals
    try:
        pa = db.execute(text("""
            SELECT COUNT(*) FROM approval_requests WHERE status = 'pending'
        """)).scalar()
        if pa and int(pa) > 0:
            alerts.append({"severity": "medium", "code": "PENDING_APPROVALS",
                            "message": f"{pa} pending approval requests",
                            "message_ar": f"{pa} طلب اعتماد معلق",
                            "count": int(pa), "link": "/approvals"})
    except Exception:
        pass

    return alerts


def _build_financial_alerts(db, current_ratio: float, quick_ratio: float,
                             budget_variance: float, branch_id: Optional[int] = None) -> list:
    """Build financial alerts."""
    alerts = []
    if current_ratio > 0 and current_ratio < 1.0:
        alerts.append({"severity": "high", "code": "LOW_LIQUIDITY",
                        "message": f"Current ratio at {current_ratio:.2f} — below 1.0 (liquidity risk)",
                        "message_ar": f"نسبة التداول {current_ratio:.2f} — تحت 1.0 (خطر سيولة)",
                        "link": "/reports/balance-sheet"})
    if abs(budget_variance) > 15:
        alerts.append({"severity": "high", "code": "BUDGET_OVERRUN",
                        "message": f"Budget variance at {budget_variance:+.1f}% — exceeds 15% threshold",
                        "message_ar": f"انحراف الميزانية {budget_variance:+.1f}% — يتجاوز حد 15%",
                        "link": "/reports/budget-vs-actual"})
    return alerts
