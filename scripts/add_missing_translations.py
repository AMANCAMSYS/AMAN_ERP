#!/usr/bin/env python3
"""
Script to add all missing translation keys to en.json and ar.json.
Based on comprehensive audit of t() calls in frontend code.
"""
import json
import sys
import os

# All missing translation keys organized by module
MISSING_KEYS = {
    # ===== ACCOUNTING MODULE (46 keys) =====
    "accounting": {
        "active_schedules": {"en": "Active Schedules", "ar": "الجداول النشطة"},
        "add_ic_transaction": {"en": "Add IC Transaction", "ar": "إضافة معاملة بين الشركات"},
        "add_schedule": {"en": "Add Schedule", "ar": "إضافة جدول"},
        "auto_generated": {"en": "Auto Generated", "ar": "مولّد تلقائياً"},
        "completed_schedules": {"en": "Completed Schedules", "ar": "الجداول المكتملة"},
        "confirm_process": {"en": "Confirm Process", "ar": "تأكيد المعالجة"},
        "confirm_recognize": {"en": "Confirm Recognize", "ar": "تأكيد الاعتراف"},
        "contract_id": {"en": "Contract ID", "ar": "رقم العقد"},
        "deferred_revenue": {"en": "Deferred Revenue", "ar": "الإيرادات المؤجلة"},
        "elimination_by_company": {"en": "Elimination by Company", "ar": "الاستبعاد حسب الشركة"},
        "elimination_report": {"en": "Elimination Report", "ar": "تقرير الاستبعاد"},
        "ic_purchase": {"en": "IC Purchase", "ar": "مشتريات بين الشركات"},
        "ic_sale": {"en": "IC Sale", "ar": "مبيعات بين الشركات"},
        "ic_service": {"en": "IC Service", "ar": "خدمات بين الشركات"},
        "ic_transactions": {"en": "IC Transactions", "ar": "المعاملات بين الشركات"},
        "ic_transfer": {"en": "IC Transfer", "ar": "تحويل بين الشركات"},
        "intercompany": {"en": "Intercompany", "ar": "بين الشركات"},
        "intercompany_desc": {"en": "Intercompany Transactions", "ar": "المعاملات بين الشركات"},
        "invoice_id": {"en": "Invoice ID", "ar": "رقم الفاتورة"},
        "method": {"en": "Method", "ar": "الطريقة"},
        "milestone": {"en": "Milestone", "ar": "مرحلة"},
        "new_ic_transaction": {"en": "New IC Transaction", "ar": "معاملة جديدة بين الشركات"},
        "new_schedule": {"en": "New Schedule", "ar": "جدول جديد"},
        "pending": {"en": "Pending", "ar": "قيد الانتظار"},
        "pending_amount": {"en": "Pending Amount", "ar": "المبلغ المعلق"},
        "pending_elimination": {"en": "Pending Elimination", "ar": "استبعاد معلق"},
        "percentage_completion": {"en": "Percentage of Completion", "ar": "نسبة الإنجاز"},
        "process": {"en": "Process", "ar": "معالجة"},
        "processed": {"en": "Processed", "ar": "تمت المعالجة"},
        "processed_amount": {"en": "Processed Amount", "ar": "المبلغ المعالج"},
        "progress": {"en": "Progress", "ar": "التقدم"},
        "recognition_pct": {"en": "Recognition %", "ar": "نسبة الاعتراف"},
        "recognize": {"en": "Recognize", "ar": "اعتراف"},
        "recognized": {"en": "Recognized", "ar": "معترف به"},
        "recognized_amount": {"en": "Recognized Amount", "ar": "المبلغ المعترف به"},
        "recognized_revenue": {"en": "Recognized Revenue", "ar": "الإيرادات المعترف بها"},
        "reference": {"en": "Reference", "ar": "المرجع"},
        "revenue_desc": {"en": "Revenue Recognition Management", "ar": "إدارة الاعتراف بالإيراد"},
        "revenue_recognition": {"en": "Revenue Recognition", "ar": "الاعتراف بالإيراد"},
        "schedule": {"en": "Schedule", "ar": "جدول"},
        "schedules": {"en": "Schedules", "ar": "الجداول"},
        "straight_line": {"en": "Straight Line", "ar": "القسط الثابت"},
        "target_company": {"en": "Target Company", "ar": "الشركة المستهدفة"},
        "total_amount": {"en": "Total Amount", "ar": "المبلغ الإجمالي"},
        "total_contract_value": {"en": "Total Contract Value", "ar": "إجمالي قيمة العقد"},
        "total_eliminated": {"en": "Total Eliminated", "ar": "إجمالي المستبعد"},
        "total_intercompany": {"en": "Total Intercompany", "ar": "إجمالي بين الشركات"},
        "transaction_type": {"en": "Transaction Type", "ar": "نوع المعاملة"},
    },

    # ===== APPROVALS MODULE (3 keys) =====
    "approvals.table": {
        "configured": {"en": "Configured", "ar": "مُهيّأ"},
        "requires_action": {"en": "Requires Action", "ar": "يتطلب إجراء"},
        "total_requests": {"en": "Total Requests", "ar": "إجمالي الطلبات"},
    },

    # ===== ASSET_REPORTS MODULE (1 key) =====
    "asset_reports": {
        "report_type": {"en": "Report Type", "ar": "نوع التقرير"},
    },

    # ===== ASSETS MODULE (1 key) =====
    "assets": {
        "updated_msg": {"en": "Asset updated successfully", "ar": "تم تحديث الأصل بنجاح"},
    },

    # ===== BUYING MODULE (6 keys) =====
    "buying.payments.form": {
        "prefilled_note": {"en": "Payment details have been prefilled", "ar": "تم تعبئة تفاصيل الدفع مسبقاً"},
    },
    "buying.purchase_invoices.form": {
        "error_product_required": {"en": "Product is required", "ar": "المنتج مطلوب"},
    },
    "buying.reports.statement.filters": {
        "days": {"en": "Days", "ar": "أيام"},
    },
    "buying.suppliers.form": {
        "quick_add_group": {"en": "Quick Add Group", "ar": "إضافة مجموعة سريعة"},
        "subtitle_edit": {"en": "Edit Supplier", "ar": "تعديل المورد"},
        "subtitle_new": {"en": "New Supplier", "ar": "مورد جديد"},
    },

    # ===== COMMON MODULE (37 keys) =====
    "common": {
        "account_code": {"en": "Account Code", "ar": "رمز الحساب"},
        "account_name": {"en": "Account Name", "ar": "اسم الحساب"},
        "all_branches": {"en": "All Branches", "ar": "جميع الفروع"},
        "all_categories": {"en": "All Categories", "ar": "جميع الفئات"},
        "all_types": {"en": "All Types", "ar": "جميع الأنواع"},
        "apply": {"en": "Apply", "ar": "تطبيق"},
        "calculating": {"en": "Calculating...", "ar": "جاري الحساب..."},
        "clear_filters": {"en": "Clear Filters", "ar": "مسح الفلاتر"},
        "confirmed": {"en": "Confirmed", "ar": "مؤكد"},
        "expenses": {"en": "Expenses", "ar": "المصروفات"},
        "generate": {"en": "Generate", "ar": "إنشاء"},
        "items": {"en": "Items", "ar": "العناصر"},
        "net_income": {"en": "Net Income", "ar": "صافي الدخل"},
        "optional": {"en": "Optional", "ar": "اختياري"},
        "other": {"en": "Other", "ar": "أخرى"},
        "phone": {"en": "Phone", "ar": "الهاتف"},
        "post": {"en": "Post", "ar": "ترحيل"},
        "posting": {"en": "Posting...", "ar": "جاري الترحيل..."},
        "qty": {"en": "Qty", "ar": "الكمية"},
        "records": {"en": "Records", "ar": "سجلات"},
        "reports": {"en": "Reports", "ar": "التقارير"},
        "revenue": {"en": "Revenue", "ar": "الإيرادات"},
        "sending": {"en": "Sending...", "ar": "جاري الإرسال..."},
        "stage": {"en": "Stage", "ar": "المرحلة"},
        "subtotal": {"en": "Subtotal", "ar": "المجموع الفرعي"},
        "summary": {"en": "Summary", "ar": "الملخص"},
        "tax": {"en": "Tax", "ar": "الضريبة"},
        "time": {"en": "Time", "ar": "الوقت"},
        "unassigned": {"en": "Unassigned", "ar": "غير معيّن"},
        "unit_price": {"en": "Unit Price", "ar": "سعر الوحدة"},
        "unknown": {"en": "Unknown", "ar": "غير معروف"},
        "uploading": {"en": "Uploading...", "ar": "جاري الرفع..."},
        "user": {"en": "User", "ar": "المستخدم"},
        "value": {"en": "Value", "ar": "القيمة"},
    },
    # common.status sub-keys
    "common.status": {
        "draft": {"en": "Draft", "ar": "مسودة"},
        "posted": {"en": "Posted", "ar": "مرحّل"},
        "title": {"en": "Status", "ar": "الحالة"},
    },

    # ===== CRM MODULE (109 keys) =====
    "crm": {
        "active_deals": {"en": "Active Deals", "ar": "الصفقات النشطة"},
        "actual_value": {"en": "Actual Value", "ar": "القيمة الفعلية"},
        "added_at": {"en": "Added At", "ar": "تاريخ الإضافة"},
        "advanced_tools": {"en": "Advanced Tools", "ar": "أدوات متقدمة"},
        "all_grades": {"en": "All Grades", "ar": "جميع الدرجات"},
        "analytics_desc": {"en": "Pipeline Analytics", "ar": "تحليلات خط الأنابيب"},
        "auto": {"en": "Auto", "ar": "تلقائي"},
        "auto_assign": {"en": "Auto Assign", "ar": "تعيين تلقائي"},
        "avg_cost_conversion": {"en": "Avg. Cost per Conversion", "ar": "متوسط تكلفة التحويل"},
        "avg_days_close": {"en": "Avg. Days to Close", "ar": "متوسط أيام الإغلاق"},
        "avg_deal": {"en": "Avg. Deal Value", "ar": "متوسط قيمة الصفقة"},
        "best_case": {"en": "Best Case", "ar": "أفضل حالة"},
        "calculate_scores": {"en": "Calculate Scores", "ar": "حساب الدرجات"},
        "campaign_performance": {"en": "Campaign Performance", "ar": "أداء الحملة"},
        "campaign_roi_tab": {"en": "Campaign ROI", "ar": "عائد استثمار الحملة"},
        "campaigns_subtitle": {"en": "Marketing Campaigns", "ar": "الحملات التسويقية"},
        "campaigns_title": {"en": "Campaigns", "ar": "الحملات"},
        "click_rate": {"en": "Click Rate", "ar": "معدل النقر"},
        "clicks": {"en": "Clicks", "ar": "النقرات"},
        "color": {"en": "Color", "ar": "اللون"},
        "commit_value": {"en": "Commit Value", "ar": "قيمة الالتزام"},
        "contacts_desc": {"en": "Manage Contacts", "ar": "إدارة جهات الاتصال"},
        "contacts_list": {"en": "Contacts List", "ar": "قائمة جهات الاتصال"},
        "conversion_tab": {"en": "Conversion", "ar": "التحويل"},
        "convert_error": {"en": "Conversion Error", "ar": "خطأ في التحويل"},
        "convert_no_customer": {"en": "No customer linked", "ar": "لا يوجد عميل مرتبط"},
        "convert_quotation_short": {"en": "Convert to Quotation", "ar": "تحويل إلى عرض سعر"},
        "convert_success": {"en": "Converted Successfully", "ar": "تم التحويل بنجاح"},
        "convert_to_quotation": {"en": "Convert to Quotation", "ar": "تحويل إلى عرض سعر"},
        "cost_per_conv": {"en": "Cost per Conversion", "ar": "تكلفة التحويل"},
        "created": {"en": "Created", "ar": "تم الإنشاء"},
        "customer_id": {"en": "Customer ID", "ar": "رقم العميل"},
        "customer_support": {"en": "Customer Support", "ar": "دعم العملاء"},
        "dashboard_subtitle": {"en": "CRM Dashboard", "ar": "لوحة تحكم CRM"},
        "deals_count": {"en": "Deals Count", "ar": "عدد الصفقات"},
        "deals_won": {"en": "Deals Won", "ar": "الصفقات المكسوبة"},
        "decision_maker": {"en": "Decision Maker", "ar": "صاحب القرار"},
        "edit_campaign": {"en": "Edit Campaign", "ar": "تعديل الحملة"},
        "field": {"en": "Field", "ar": "الحقل"},
        "field_email": {"en": "Email", "ar": "البريد الإلكتروني"},
        "field_phone": {"en": "Phone", "ar": "الهاتف"},
        "field_probability": {"en": "Probability", "ar": "الاحتمالية"},
        "field_source": {"en": "Source", "ar": "المصدر"},
        "field_stage": {"en": "Stage", "ar": "المرحلة"},
        "forecast_by_month": {"en": "Forecast by Month", "ar": "التنبؤ حسب الشهر"},
        "forecast_scenarios": {"en": "Forecast Scenarios", "ar": "سيناريوهات التنبؤ"},
        "forecasts_desc": {"en": "Sales Forecasts", "ar": "توقعات المبيعات"},
        "grade": {"en": "Grade", "ar": "الدرجة"},
        "grade_average": {"en": "Average", "ar": "متوسط"},
        "grade_excellent": {"en": "Excellent", "ar": "ممتاز"},
        "grade_good": {"en": "Good", "ar": "جيد"},
        "grade_low": {"en": "Low", "ar": "منخفض"},
        "historical_actuals": {"en": "Historical Actuals", "ar": "البيانات الفعلية التاريخية"},
        "is_decision_maker": {"en": "Is Decision Maker", "ar": "صاحب القرار"},
        "is_primary": {"en": "Is Primary", "ar": "أساسي"},
        "kb_article_title": {"en": "Article Title", "ar": "عنوان المقال"},
        "kb_author": {"en": "Author", "ar": "الكاتب"},
        "kb_category": {"en": "Category", "ar": "الفئة"},
        "kb_content": {"en": "Content", "ar": "المحتوى"},
        "kb_draft": {"en": "Draft", "ar": "مسودة"},
        "kb_edit": {"en": "Edit Article", "ar": "تعديل المقال"},
        "kb_new": {"en": "New Article", "ar": "مقال جديد"},
        "kb_no_articles": {"en": "No articles found", "ar": "لا توجد مقالات"},
        "kb_publish": {"en": "Publish", "ar": "نشر"},
        "kb_published": {"en": "Published", "ar": "منشور"},
        "kb_search": {"en": "Search articles...", "ar": "البحث في المقالات..."},
        "kb_subtitle": {"en": "Knowledge Base", "ar": "قاعدة المعرفة"},
        "kb_tags": {"en": "Tags", "ar": "الوسوم"},
        "kb_tags_placeholder": {"en": "Enter tags...", "ar": "أدخل الوسوم..."},
        "kb_title": {"en": "Knowledge Base", "ar": "قاعدة المعرفة"},
        "kb_views": {"en": "Views", "ar": "المشاهدات"},
        "last_scored": {"en": "Last Scored", "ar": "آخر تقييم"},
        "lead_score_distribution": {"en": "Lead Score Distribution", "ar": "توزيع درجات العملاء المحتملين"},
        "lead_scoring_desc": {"en": "Lead Scoring Configuration", "ar": "إعدادات تقييم العملاء المحتملين"},
        "loss_rate": {"en": "Loss Rate", "ar": "معدل الخسارة"},
        "lost": {"en": "Lost", "ar": "خسارة"},
        "lost_deals": {"en": "Lost Deals", "ar": "الصفقات الخاسرة"},
        "marketing": {"en": "Marketing", "ar": "التسويق"},
        "monthly_trend": {"en": "Monthly Trend", "ar": "الاتجاه الشهري"},
        "most_likely": {"en": "Most Likely", "ar": "الأكثر احتمالاً"},
        "new_campaign": {"en": "New Campaign", "ar": "حملة جديدة"},
        "new_contact": {"en": "New Contact", "ar": "جهة اتصال جديدة"},
        "new_rule": {"en": "New Rule", "ar": "قاعدة جديدة"},
        "new_segment": {"en": "New Segment", "ar": "شريحة جديدة"},
        "no_campaigns": {"en": "No campaigns found", "ar": "لا توجد حملات"},
        "no_contacts": {"en": "No contacts found", "ar": "لا توجد جهات اتصال"},
        "no_members": {"en": "No members found", "ar": "لا يوجد أعضاء"},
        "no_rules": {"en": "No rules configured", "ar": "لا توجد قواعد مُهيّأة"},
        "no_scores": {"en": "No scores calculated", "ar": "لا توجد درجات محسوبة"},
        "no_segments": {"en": "No segments found", "ar": "لا توجد شرائح"},
        "op_contains": {"en": "Contains", "ar": "يحتوي"},
        "op_equals": {"en": "Equals", "ar": "يساوي"},
        "op_exists": {"en": "Exists", "ar": "موجود"},
        "op_gt": {"en": "Greater Than", "ar": "أكبر من"},
        "op_lt": {"en": "Less Than", "ar": "أقل من"},
        "open_rate": {"en": "Open Rate", "ar": "معدل الفتح"},
        "opens": {"en": "Opens", "ar": "فتحات"},
        "opportunity": {"en": "Opportunity", "ar": "فرصة"},
        "overall_rate": {"en": "Overall Rate", "ar": "المعدل الإجمالي"},
        "period": {"en": "Period", "ar": "الفترة"},
        "pipeline_analytics": {"en": "Pipeline Analytics", "ar": "تحليلات خط الأنابيب"},
        "pipeline_tab": {"en": "Pipeline", "ar": "خط الأنابيب"},
        "primary": {"en": "Primary", "ar": "أساسي"},
        "probability_50": {"en": "Probability ≥ 50%", "ar": "احتمالية ≥ ٥٠٪"},
        "probability_75": {"en": "Probability ≥ 75%", "ar": "احتمالية ≥ ٧٥٪"},
        "role": {"en": "Role", "ar": "الدور"},
        "rule_name": {"en": "Rule Name", "ar": "اسم القاعدة"},
        "sales_activities": {"en": "Sales Activities", "ar": "الأنشطة البيعية"},
        "sales_funnel": {"en": "Sales Funnel", "ar": "قمع المبيعات"},
        "score": {"en": "Score", "ar": "الدرجة"},
        "segment_members": {"en": "Segment Members", "ar": "أعضاء الشريحة"},
        "segments_desc": {"en": "Customer Segments", "ar": "شرائح العملاء"},
        "sent": {"en": "Sent", "ar": "مُرسل"},
        "source_analysis": {"en": "Source Analysis", "ar": "تحليل المصادر"},
        "stage_distribution": {"en": "Stage Distribution", "ar": "توزيع المراحل"},
        "target_audience": {"en": "Target Audience", "ar": "الجمهور المستهدف"},
        "target_audience_placeholder": {"en": "Enter target audience...", "ar": "أدخل الجمهور المستهدف..."},
        "top_performers": {"en": "Top Performers", "ar": "الأفضل أداءً"},
        "total_budget": {"en": "Total Budget", "ar": "إجمالي الميزانية"},
        "total_campaigns": {"en": "Total Campaigns", "ar": "إجمالي الحملات"},
        "total_closed": {"en": "Total Closed", "ar": "إجمالي المُغلق"},
        "total_conversions": {"en": "Total Conversions", "ar": "إجمالي التحويلات"},
        "total_investment": {"en": "Total Investment", "ar": "إجمالي الاستثمار"},
        "total_value": {"en": "Total Value", "ar": "القيمة الإجمالية"},
        "total_won": {"en": "Total Won", "ar": "إجمالي المكسوب"},
        "type": {"en": "Type", "ar": "النوع"},
        "weighted_avg": {"en": "Weighted Average", "ar": "المتوسط المرجح"},
        "wins": {"en": "Wins", "ar": "مكاسب"},
        "won_deals": {"en": "Won Deals", "ar": "الصفقات المكسوبة"},
        "won_value": {"en": "Won Value", "ar": "قيمة المكسوب"},
        "won_vs_lost": {"en": "Won vs Lost", "ar": "مكسوب مقابل خاسر"},
    },

    # ===== EXPENSES MODULE (2 keys) =====
    "expenses": {
        "quick_actions": {"en": "Quick Actions", "ar": "إجراءات سريعة"},
        "status_summary": {"en": "Status Summary", "ar": "ملخص الحالة"},
    },

    # ===== HR MODULE (9 keys) =====
    "hr.employees": {
        "currency_auto": {"en": "Currency (auto)", "ar": "العملة (تلقائي)"},
        "nationality": {"en": "Nationality", "ar": "الجنسية"},
        "salary_currency": {"en": "Salary Currency", "ar": "عملة الراتب"},
    },
    "hr.payroll": {
        "confirm_generate": {"en": "Confirm Generate", "ar": "تأكيد الإنشاء"},
        "confirm_post": {"en": "Confirm Post", "ar": "تأكيد الترحيل"},
        "generate": {"en": "Generate", "ar": "إنشاء"},
        "generate_hint": {"en": "Generate payroll entries", "ar": "إنشاء قيود الرواتب"},
        "no_entries": {"en": "No entries", "ar": "لا توجد قيود"},
        "period_not_found": {"en": "Period not found", "ar": "الفترة غير موجودة"},
    },

    # ===== MANUFACTURING MODULE (47 keys) =====
    "manufacturing.analytics": {
        "completed_ops": {"en": "Completed Operations", "ar": "العمليات المكتملة"},
        "completed_orders": {"en": "Completed Orders", "ar": "الأوامر المكتملة"},
        "cost_analysis": {"en": "Cost Analysis", "ar": "تحليل التكاليف"},
        "cost_details": {"en": "Cost Details", "ar": "تفاصيل التكاليف"},
        "in_progress_orders": {"en": "In Progress Orders", "ar": "الأوامر قيد التنفيذ"},
        "labor_cost": {"en": "Labor Cost", "ar": "تكلفة العمالة"},
        "maintenance_due": {"en": "Maintenance Due", "ar": "صيانة مستحقة"},
        "material_cost": {"en": "Material Cost", "ar": "تكلفة المواد"},
        "order_count": {"en": "Order Count", "ar": "عدد الأوامر"},
        "overhead_cost": {"en": "Overhead Cost", "ar": "التكاليف غير المباشرة"},
        "produced_qty": {"en": "Produced Quantity", "ar": "الكمية المنتجة"},
        "run_hours": {"en": "Run Hours", "ar": "ساعات التشغيل"},
        "status_distribution": {"en": "Status Distribution", "ar": "توزيع الحالات"},
        "subtitle": {"en": "Production Analytics", "ar": "تحليلات الإنتاج"},
        "title": {"en": "Production Analytics", "ar": "تحليلات الإنتاج"},
        "top_products": {"en": "Top Products", "ar": "أعلى المنتجات"},
        "total_cost": {"en": "Total Cost", "ar": "التكلفة الإجمالية"},
        "total_operations": {"en": "Total Operations", "ar": "إجمالي العمليات"},
        "total_orders": {"en": "Total Orders", "ar": "إجمالي الأوامر"},
        "total_output": {"en": "Total Output", "ar": "إجمالي الإنتاج"},
        "unit_cost": {"en": "Unit Cost", "ar": "تكلفة الوحدة"},
        "utilization": {"en": "Utilization", "ar": "نسبة الاستخدام"},
        "wc_efficiency": {"en": "Work Center Efficiency", "ar": "كفاءة مراكز العمل"},
    },
    "manufacturing.direct_labor": {
        "actual_hours": {"en": "Actual Hours", "ar": "الساعات الفعلية"},
        "cost_per_hour": {"en": "Cost per Hour", "ar": "التكلفة لكل ساعة"},
        "cost_per_unit": {"en": "Cost per Unit", "ar": "التكلفة لكل وحدة"},
        "details": {"en": "Details", "ar": "التفاصيل"},
        "efficiency": {"en": "Efficiency", "ar": "الكفاءة"},
        "labor_cost": {"en": "Labor Cost", "ar": "تكلفة العمالة"},
        "no_data": {"en": "No data available", "ar": "لا توجد بيانات"},
        "operations_count": {"en": "Operations Count", "ar": "عدد العمليات"},
        "planned_hours": {"en": "Planned Hours", "ar": "الساعات المخططة"},
        "qty": {"en": "Quantity", "ar": "الكمية"},
        "subtitle": {"en": "Direct Labor Report", "ar": "تقرير العمالة المباشرة"},
        "title": {"en": "Direct Labor Report", "ar": "تقرير العمالة المباشرة"},
        "total_cost": {"en": "Total Cost", "ar": "التكلفة الإجمالية"},
        "total_hours": {"en": "Total Hours", "ar": "إجمالي الساعات"},
        "wc_summary": {"en": "Work Center Summary", "ar": "ملخص مراكز العمل"},
    },
    "manufacturing": {
        "master_data": {"en": "Master Data", "ar": "البيانات الرئيسية"},
        "order_number": {"en": "Order Number", "ar": "رقم الأمر"},
        "production": {"en": "Production", "ar": "الإنتاج"},
        # Asymmetric: exist in ar but not en
        "view_all_job_cards_short": {"en": "View All Job Cards", "ar": None},  # ar already exists
        "wc_cost_center": {"en": "Cost Center", "ar": None},
        "wc_cost_per_hour": {"en": "Cost Per Hour", "ar": None},
        "wc_location": {"en": "Location", "ar": None},
        "wc_overhead_account": {"en": "Overhead Account", "ar": None},
        "wc_status": {"en": "Status", "ar": None},
    },
    "manufacturing.work_orders_report": {
        "completion_rate": {"en": "Completion Rate", "ar": "معدل الإنجاز"},
        "orders_list": {"en": "Orders List", "ar": "قائمة الأوامر"},
        "produced": {"en": "Produced", "ar": "المنتج"},
        "progress": {"en": "Progress", "ar": "التقدم"},
        "subtitle": {"en": "Work Order Status Report", "ar": "تقرير حالة أوامر العمل"},
        "title": {"en": "Work Order Status Report", "ar": "تقرير حالة أوامر العمل"},
    },

    # ===== POS MODULE (19 keys) =====
    "pos.home": {
        "customer_display": {"en": "Customer Display", "ar": "شاشة العميل"},
        "offline_mode": {"en": "Offline Mode", "ar": "وضع عدم الاتصال"},
        "thermal_print": {"en": "Thermal Print", "ar": "الطباعة الحرارية"},
    },
    "pos.offline": {
        "auto_sync": {"en": "Auto Sync", "ar": "مزامنة تلقائية"},
        "connection": {"en": "Connection", "ar": "الاتصال"},
        "created": {"en": "Created", "ar": "تم الإنشاء"},
        "details": {"en": "Details", "ar": "التفاصيل"},
        "disabled": {"en": "Disabled", "ar": "معطل"},
        "disconnected": {"en": "Disconnected", "ar": "غير متصل"},
        "enabled": {"en": "Enabled", "ar": "مفعل"},
        "failed": {"en": "Failed", "ar": "فشل"},
        "items": {"en": "Items", "ar": "العناصر"},
        "online": {"en": "Online", "ar": "متصل"},
        "pending_list": {"en": "Pending List", "ar": "قائمة المعلقة"},
        "pending_orders": {"en": "Pending Orders", "ar": "الطلبات المعلقة"},
        "sync_log": {"en": "Sync Log", "ar": "سجل المزامنة"},
        "sync_now": {"en": "Sync Now", "ar": "مزامنة الآن"},
        "synced": {"en": "Synced", "ar": "تمت المزامنة"},
        "time": {"en": "Time", "ar": "الوقت"},
    },

    # ===== PROJECTS MODULE (4 keys) =====
    "projects": {
        "management": {"en": "Management", "ar": "الإدارة"},
        "overview": {"en": "Overview", "ar": "نظرة عامة"},
    },
    "projects.reports": {
        "financials": {"en": "Financial Reports", "ar": "التقارير المالية"},
        "resources": {"en": "Resource Reports", "ar": "تقارير الموارد"},
    },

    # ===== REPORTS MODULE (1 key) =====
    "reports.sharing": {
        "shared_subtitle": {"en": "Shared Reports", "ar": "التقارير المشتركة"},
    },

    # ===== SALES MODULE (11 keys) =====
    "sales.invoices": {
        "payment_method": {"en": "Payment Method", "ar": "طريقة الدفع"},
    },
    "sales.print": {
        "buyer": {"en": "Buyer", "ar": "المشتري"},
        "seller": {"en": "Seller", "ar": "البائع"},
        "taxable_amount": {"en": "Taxable Amount", "ar": "المبلغ الخاضع للضريبة"},
        "thank_you": {"en": "Thank you for your business", "ar": "شكراً لتعاملكم معنا"},
        "title": {"en": "Tax Invoice", "ar": "فاتورة ضريبية"},
        "total_with_vat": {"en": "Total with VAT", "ar": "الإجمالي شامل الضريبة"},
        "vat_amount": {"en": "VAT Amount", "ar": "مبلغ الضريبة"},
        "vat_no": {"en": "VAT No.", "ar": "الرقم الضريبي"},
        "zatca_notice": {"en": "ZATCA Compliant Invoice", "ar": "فاتورة متوافقة مع هيئة الزكاة والضريبة والجمارك"},
        "zatca_simplified": {"en": "Simplified Tax Invoice", "ar": "فاتورة ضريبية مبسطة"},
    },

    # ===== STATUS MODULE (2 keys) =====
    "status": {
        "completed": {"en": "Completed", "ar": "مكتمل"},
        "in_progress": {"en": "In Progress", "ar": "قيد التنفيذ"},
    },

    # ===== STOCK MODULE (5 keys) =====
    "stock.batch": {
        "days_remaining": {"en": "Days Remaining", "ar": "الأيام المتبقية"},
        "expired_since": {"en": "Expired Since", "ar": "منتهي الصلاحية منذ"},
    },
    "stock.cycle": {
        "selected_products": {"en": "Selected Products", "ar": "المنتجات المحددة"},
    },
    "stock.serial": {
        "create_n": {"en": "Create Serial Numbers", "ar": "إنشاء أرقام تسلسلية"},
        "will_create": {"en": "Will Create", "ar": "سيتم إنشاء"},
    },

    # ===== TAXES MODULE (4 keys) =====
    "taxes": {
        "reports_analysis": {"en": "Reports & Analysis", "ar": "التقارير والتحليل"},
        "returns_management": {"en": "Returns Management", "ar": "إدارة الإقرارات"},
        "settings_tools": {"en": "Settings & Tools", "ar": "الإعدادات والأدوات"},
        "tax_calendar": {"en": "Tax Calendar", "ar": "التقويم الضريبي"},
    },

    # ===== TREASURY MODULE (1 key) =====
    "treasury": {
        "error_same_account": {"en": "Cannot transfer to the same account", "ar": "لا يمكن التحويل إلى نفس الحساب"},
    },

    # ===== WHT MODULE (1 key) =====
    "wht": {
        "error_calculating": {"en": "Error calculating WHT", "ar": "خطأ في حساب ضريبة الاستقطاع"},
    },
}

# Additional comprehensive accounting/financial terms
ACCOUNTING_TERMS = {
    "accounting": {
        # Financial Statements (IAS 1)
        "chart_of_accounts": {"en": "Chart of Accounts", "ar": "دليل الحسابات"},
        "cost_of_goods_sold": {"en": "Cost of Goods Sold (COGS)", "ar": "تكلفة البضاعة المباعة"},
        "double_entry": {"en": "Double Entry", "ar": "القيد المزدوج"},
        "accrual": {"en": "Accrual", "ar": "الاستحقاق"},
        "accrued_expenses": {"en": "Accrued Expenses", "ar": "المصروفات المستحقة"},
        "accrued_revenue": {"en": "Accrued Revenue", "ar": "الإيرادات المستحقة"},
        "provision": {"en": "Provision", "ar": "المخصص"},
        "provisions": {"en": "Provisions", "ar": "المخصصات"},
        "prepaid_expenses": {"en": "Prepaid Expenses", "ar": "المصروفات المدفوعة مقدماً"},
        "unearned_revenue": {"en": "Unearned Revenue", "ar": "الإيرادات غير المكتسبة"},

        # Equity & Capital
        "shareholders_equity": {"en": "Shareholders' Equity", "ar": "حقوق المساهمين"},
        "paid_in_capital": {"en": "Paid-in Capital", "ar": "رأس المال المدفوع"},
        "share_capital": {"en": "Share Capital", "ar": "رأس مال الأسهم"},
        "capital_reserve": {"en": "Capital Reserve", "ar": "احتياطي رأسمالي"},
        "statutory_reserve": {"en": "Statutory Reserve", "ar": "الاحتياطي النظامي"},
        "dividends": {"en": "Dividends", "ar": "توزيعات الأرباح"},

        # Financial Ratios & KPIs
        "working_capital": {"en": "Working Capital", "ar": "رأس المال العامل"},
        "liquidity_ratio": {"en": "Liquidity Ratio", "ar": "نسبة السيولة"},
        "current_ratio": {"en": "Current Ratio", "ar": "النسبة الجارية"},
        "quick_ratio": {"en": "Quick Ratio", "ar": "نسبة السيولة السريعة"},
        "debt_ratio": {"en": "Debt Ratio", "ar": "نسبة المديونية"},
        "debt_to_equity": {"en": "Debt to Equity Ratio", "ar": "نسبة الدين إلى حقوق الملكية"},
        "ebitda": {"en": "EBITDA", "ar": "الأرباح قبل الفوائد والضرائب والاستهلاك والإطفاء"},
        "operating_income": {"en": "Operating Income", "ar": "الدخل التشغيلي"},
        "gross_profit": {"en": "Gross Profit", "ar": "مجمل الربح"},
        "net_profit_margin": {"en": "Net Profit Margin", "ar": "هامش صافي الربح"},
        "return_on_assets": {"en": "Return on Assets (ROA)", "ar": "العائد على الأصول"},
        "return_on_equity": {"en": "Return on Equity (ROE)", "ar": "العائد على حقوق الملكية"},
        "earnings_per_share": {"en": "Earnings Per Share (EPS)", "ar": "ربحية السهم"},

        # International Standards
        "gaap": {"en": "GAAP", "ar": "المبادئ المحاسبية المقبولة عموماً"},
        "ifrs_compliance": {"en": "IFRS Compliance", "ar": "الامتثال للمعايير الدولية للتقارير المالية"},
        "ias_standards": {"en": "IAS Standards", "ar": "معايير المحاسبة الدولية"},
        "socpa": {"en": "SOCPA", "ar": "الهيئة السعودية للمراجعين والمحاسبين"},

        # Cash Flow (IAS 7)
        "operating_activities": {"en": "Operating Activities", "ar": "الأنشطة التشغيلية"},
        "investing_activities": {"en": "Investing Activities", "ar": "الأنشطة الاستثمارية"},
        "financing_activities": {"en": "Financing Activities", "ar": "الأنشطة التمويلية"},
        "free_cash_flow": {"en": "Free Cash Flow", "ar": "التدفق النقدي الحر"},

        # Cost Accounting
        "direct_costs": {"en": "Direct Costs", "ar": "التكاليف المباشرة"},
        "indirect_costs": {"en": "Indirect Costs", "ar": "التكاليف غير المباشرة"},
        "fixed_costs": {"en": "Fixed Costs", "ar": "التكاليف الثابتة"},
        "variable_costs": {"en": "Variable Costs", "ar": "التكاليف المتغيرة"},
        "overhead": {"en": "Overhead", "ar": "المصاريف العامة"},
        "break_even_point": {"en": "Break-Even Point", "ar": "نقطة التعادل"},
        "contribution_margin": {"en": "Contribution Margin", "ar": "هامش المساهمة"},
        "variance_analysis": {"en": "Variance Analysis", "ar": "تحليل الانحرافات"},

        # Audit & Compliance
        "internal_audit": {"en": "Internal Audit", "ar": "المراجعة الداخلية"},
        "external_audit": {"en": "External Audit", "ar": "المراجعة الخارجية"},
        "audit_trail": {"en": "Audit Trail", "ar": "مسار المراجعة"},
        "materiality": {"en": "Materiality", "ar": "الأهمية النسبية"},
        "going_concern": {"en": "Going Concern", "ar": "الاستمرارية"},
        "fair_value": {"en": "Fair Value", "ar": "القيمة العادلة"},
        "book_value": {"en": "Book Value", "ar": "القيمة الدفترية"},
        "carrying_amount": {"en": "Carrying Amount", "ar": "المبلغ المسجل"},
        "impairment": {"en": "Impairment", "ar": "انخفاض القيمة"},
        "goodwill": {"en": "Goodwill", "ar": "الشهرة"},
        "contingent_liability": {"en": "Contingent Liability", "ar": "التزام محتمل"},

        # Tax Terms
        "withholding_tax": {"en": "Withholding Tax", "ar": "ضريبة الاستقطاع"},
        "tax_base": {"en": "Tax Base", "ar": "الوعاء الضريبي"},
        "tax_assessment": {"en": "Tax Assessment", "ar": "الربط الضريبي"},
        "tax_exemption": {"en": "Tax Exemption", "ar": "الإعفاء الضريبي"},
        "transfer_pricing": {"en": "Transfer Pricing", "ar": "التسعير التحويلي"},
    },
}


def set_nested_key(data, key_path, value):
    """Set a nested key in a dict using dot notation, creating intermediary dicts as needed."""
    keys = key_path.split(".")
    d = data
    for k in keys[:-1]:
        if k not in d:
            d[k] = {}
        elif not isinstance(d[k], dict):
            # Key exists as scalar, convert to dict
            d[k] = {}
        d = d[k]
    final_key = keys[-1]
    if final_key not in d:
        d[final_key] = value


def get_nested_key(data, key_path):
    """Get a nested key value using dot notation. Returns None if not found."""
    keys = key_path.split(".")
    d = data
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def main():
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    en_path = os.path.join(base_path, "frontend", "src", "locales", "en.json")
    ar_path = os.path.join(base_path, "frontend", "src", "locales", "ar.json")

    # Load existing files
    with open(en_path, "r", encoding="utf-8") as f:
        en_data = json.load(f)
    with open(ar_path, "r", encoding="utf-8") as f:
        ar_data = json.load(f)

    en_added = 0
    ar_added = 0
    skipped = 0

    # Process MISSING_KEYS
    for prefix, keys in MISSING_KEYS.items():
        for key, translations in keys.items():
            full_key = f"{prefix}.{key}"
            en_val = translations.get("en")
            ar_val = translations.get("ar")

            # Add to en.json if missing
            if en_val is not None:
                existing = get_nested_key(en_data, full_key)
                if existing is None:
                    set_nested_key(en_data, full_key, en_val)
                    en_added += 1
                else:
                    skipped += 1

            # Add to ar.json if missing (None means it already exists)
            if ar_val is not None:
                existing = get_nested_key(ar_data, full_key)
                if existing is None:
                    set_nested_key(ar_data, full_key, ar_val)
                    ar_added += 1
                else:
                    skipped += 1

    # Also add common.not_set to ar.json (asymmetric)
    if get_nested_key(ar_data, "common.not_set") is None:
        set_nested_key(ar_data, "common.not_set", "غير محدد")
        ar_added += 1

    # Process ACCOUNTING_TERMS
    for prefix, keys in ACCOUNTING_TERMS.items():
        for key, translations in keys.items():
            full_key = f"{prefix}.{key}"
            en_val = translations.get("en")
            ar_val = translations.get("ar")

            if en_val is not None:
                existing = get_nested_key(en_data, full_key)
                if existing is None:
                    set_nested_key(en_data, full_key, en_val)
                    en_added += 1

            if ar_val is not None:
                existing = get_nested_key(ar_data, full_key)
                if existing is None:
                    set_nested_key(ar_data, full_key, ar_val)
                    ar_added += 1

    # Write back
    with open(en_path, "w", encoding="utf-8") as f:
        json.dump(en_data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(ar_path, "w", encoding="utf-8") as f:
        json.dump(ar_data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"✅ Added {en_added} keys to en.json")
    print(f"✅ Added {ar_added} keys to ar.json")
    print(f"⏭️  Skipped {skipped} already-existing keys")
    print("Done!")


if __name__ == "__main__":
    main()
