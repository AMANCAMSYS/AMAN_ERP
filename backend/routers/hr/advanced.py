"""
Advanced HR Router - Phase 4
الموارد البشرية المتقدمة: هياكل الرواتب، مكونات الراتب، العمل الإضافي، GOSI، المستندات، تقييم الأداء، التدريب، المخالفات، العهد
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from database import get_db_connection
from routers.auth import get_current_user, UserResponse
from utils.permissions import require_permission, require_module
from utils.exports import generate_excel, generate_pdf, create_export_response

from schemas.hr_advanced import (
    SalaryStructureCreate, SalaryStructureUpdate, SalaryStructureResponse,
    SalaryComponentCreate, SalaryComponentUpdate, SalaryComponentResponse,
    EmployeeSalaryComponentCreate, EmployeeSalaryComponentResponse,
    OvertimeRequestCreate, OvertimeRequestUpdate, OvertimeRequestResponse,
    GOSISettingsCreate, GOSISettingsUpdate, GOSISettingsResponse, GOSICalculationResponse,
    EmployeeDocumentCreate, EmployeeDocumentUpdate, EmployeeDocumentResponse,
    PerformanceReviewCreate, PerformanceReviewUpdate, PerformanceReviewResponse,
    TrainingProgramCreate, TrainingProgramUpdate, TrainingProgramResponse,
    TrainingParticipantCreate, TrainingParticipantUpdate, TrainingParticipantResponse,
    ViolationCreate, ViolationUpdate, ViolationResponse,
    CustodyCreate, CustodyUpdate, CustodyResponse,
)

router = APIRouter(prefix="/hr-advanced", tags=["HR Advanced - الموارد البشرية المتقدمة"], dependencies=[Depends(require_module("hr"))])


# =============================================
# هياكل الرواتب - Salary Structures
# =============================================

@router.get("/salary-structures", response_model=List[SalaryStructureResponse], dependencies=[Depends(require_permission("hr.view"))])
def list_salary_structures(current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        rows = conn.execute(text("SELECT * FROM salary_structures ORDER BY created_at DESC")).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/salary-structures", dependencies=[Depends(require_permission("hr.manage"))])
def create_salary_structure(data: SalaryStructureCreate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        result = conn.execute(text("""
            INSERT INTO salary_structures (name, name_en, description, base_type)
            VALUES (:name, :name_en, :desc, :base_type) RETURNING id
        """), {"name": data.name, "name_en": data.name_en, "desc": data.description, "base_type": data.base_type})
        conn.commit()
        return {"id": result.scalar(), "message": "تم إنشاء هيكل الراتب بنجاح"}
    finally:
        conn.close()


@router.put("/salary-structures/{structure_id}", dependencies=[Depends(require_permission("hr.manage"))])
def update_salary_structure(structure_id: int, data: SalaryStructureUpdate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        fields, params = [], {"id": structure_id}
        for field in ["name", "name_en", "description", "base_type", "is_active"]:
            val = getattr(data, field, None)
            if val is not None:
                fields.append(f"{field} = :{field}")
                params[field] = val
        if not fields:
            raise HTTPException(status_code=400, detail="لا يوجد تعديلات")
        fields.append("updated_at = CURRENT_TIMESTAMP")
        conn.execute(text(f"UPDATE salary_structures SET {', '.join(fields)} WHERE id = :id"), params)
        conn.commit()
        return {"message": "تم التحديث بنجاح"}
    finally:
        conn.close()


@router.delete("/salary-structures/{structure_id}", dependencies=[Depends(require_permission("hr.manage"))])
def delete_salary_structure(structure_id: int, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        conn.execute(text("DELETE FROM salary_structures WHERE id = :id"), {"id": structure_id})
        conn.commit()
        return {"message": "تم الحذف بنجاح"}
    finally:
        conn.close()


# =============================================
# مكونات الراتب - Salary Components
# =============================================

@router.get("/salary-components", response_model=List[SalaryComponentResponse], dependencies=[Depends(require_permission("hr.view"))])
def list_salary_components(structure_id: Optional[int] = None, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        query = "SELECT * FROM salary_components WHERE 1=1"
        params = {}
        if structure_id:
            query += " AND structure_id = :sid"
            params["sid"] = structure_id
        query += " ORDER BY sort_order, created_at"
        rows = conn.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/salary-components", dependencies=[Depends(require_permission("hr.manage"))])
def create_salary_component(data: SalaryComponentCreate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        result = conn.execute(text("""
            INSERT INTO salary_components (name, name_en, component_type, calculation_type, percentage_of, percentage_value, formula, is_taxable, is_gosi_applicable, sort_order, structure_id)
            VALUES (:name, :name_en, :type, :calc, :pof, :pval, :formula, :tax, :gosi, :sort, :sid)
            RETURNING id
        """), {
            "name": data.name, "name_en": data.name_en, "type": data.component_type,
            "calc": data.calculation_type, "pof": data.percentage_of, "pval": data.percentage_value,
            "formula": data.formula, "tax": data.is_taxable, "gosi": data.is_gosi_applicable,
            "sort": data.sort_order, "sid": data.structure_id
        })
        conn.commit()
        return {"id": result.scalar(), "message": "تم إنشاء مكون الراتب بنجاح"}
    finally:
        conn.close()


@router.put("/salary-components/{component_id}", dependencies=[Depends(require_permission("hr.manage"))])
def update_salary_component(component_id: int, data: SalaryComponentUpdate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        fields, params = [], {"id": component_id}
        for field in ["name", "name_en", "component_type", "calculation_type", "percentage_of", "percentage_value", "formula", "is_taxable", "is_gosi_applicable", "is_active", "sort_order", "structure_id"]:
            val = getattr(data, field, None)
            if val is not None:
                fields.append(f"{field} = :{field}")
                params[field] = val
        if not fields:
            raise HTTPException(status_code=400, detail="لا يوجد تعديلات")
        conn.execute(text(f"UPDATE salary_components SET {', '.join(fields)} WHERE id = :id"), params)
        conn.commit()
        return {"message": "تم التحديث بنجاح"}
    finally:
        conn.close()


# =============================================
# ربط مكونات الراتب بالموظفين
# =============================================

@router.get("/employee-salary-components/{employee_id}", dependencies=[Depends(require_permission("hr.view"))])
def get_employee_salary_components(employee_id: int, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        rows = conn.execute(text("""
            SELECT esc.*, sc.name as component_name, sc.component_type
            FROM employee_salary_components esc
            JOIN salary_components sc ON esc.component_id = sc.id
            WHERE esc.employee_id = :eid AND esc.is_active = TRUE
            ORDER BY sc.sort_order
        """), {"eid": employee_id}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/employee-salary-components", dependencies=[Depends(require_permission("hr.manage"))])
def assign_salary_component(data: EmployeeSalaryComponentCreate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        conn.execute(text("""
            INSERT INTO employee_salary_components (employee_id, component_id, amount, is_active, effective_date)
            VALUES (:eid, :cid, :amt, :active, :date)
            ON CONFLICT (employee_id, component_id) DO UPDATE SET amount = :amt, is_active = :active, effective_date = :date
        """), {"eid": data.employee_id, "cid": data.component_id, "amt": data.amount, "active": data.is_active, "date": data.effective_date})
        conn.commit()
        return {"message": "تم تعيين مكون الراتب بنجاح"}
    finally:
        conn.close()


# =============================================
# العمل الإضافي - Overtime
# =============================================

@router.get("/overtime", response_model=List[OvertimeRequestResponse], dependencies=[Depends(require_permission("hr.view"))])
def list_overtime_requests(employee_id: Optional[int] = None, status: Optional[str] = None, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT o.*, e.first_name || ' ' || e.last_name as employee_name
            FROM overtime_requests o
            JOIN employees e ON o.employee_id = e.id
            WHERE 1=1
        """
        params = {}
        if employee_id:
            query += " AND o.employee_id = :eid"
            params["eid"] = employee_id
        if status:
            query += " AND o.status = :status"
            params["status"] = status
        query += " ORDER BY o.created_at DESC"
        rows = conn.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/overtime", dependencies=[Depends(require_permission("hr.manage"))])
def create_overtime_request(data: OvertimeRequestCreate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        # Calculate amount: (salary / 30 / 8) * hours * multiplier
        emp = conn.execute(text("SELECT salary FROM employees WHERE id = :eid"), {"eid": data.employee_id}).fetchone()
        if not emp:
            raise HTTPException(status_code=404, detail="الموظف غير موجود")

        hourly_rate = (float(emp.salary or 0) / 30) / 8
        multiplier = float(data.multiplier) if data.multiplier else (1.5 if data.overtime_type == "normal" else 2.0)
        amount = round(hourly_rate * float(data.hours) * multiplier, 2)

        result = conn.execute(text("""
            INSERT INTO overtime_requests (employee_id, request_date, overtime_date, hours, overtime_type, multiplier, calculated_amount, reason, branch_id)
            VALUES (:eid, CURRENT_DATE, :odate, :hours, :otype, :mult, :amt, :reason, :bid)
            RETURNING id
        """), {
            "eid": data.employee_id, "odate": data.overtime_date, "hours": data.hours,
            "otype": data.overtime_type, "mult": multiplier, "amt": amount,
            "reason": data.reason, "bid": data.branch_id
        })
        conn.commit()
        return {"id": result.scalar(), "calculated_amount": amount, "message": "تم إنشاء طلب العمل الإضافي"}
    finally:
        conn.close()


@router.put("/overtime/{overtime_id}/approve", dependencies=[Depends(require_permission("hr.manage"))])
def approve_overtime(overtime_id: int, data: OvertimeRequestUpdate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get("id")
        conn.execute(text("""
            UPDATE overtime_requests SET status = :status, approved_by = :uid, approved_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """), {"status": data.status, "uid": user_id, "id": overtime_id})
        conn.commit()
        return {"message": "تم تحديث حالة الطلب"}
    finally:
        conn.close()


# =============================================
# GOSI - التأمينات الاجتماعية
# =============================================

@router.get("/gosi-settings", dependencies=[Depends(require_permission("hr.view"))])
def get_gosi_settings(current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        row = conn.execute(text("SELECT * FROM gosi_settings WHERE is_active = TRUE ORDER BY id DESC LIMIT 1")).fetchone()
        if not row:
            return {"employee_share_percentage": 9.75, "employer_share_percentage": 11.75, "occupational_hazard_percentage": 2.0, "max_contributable_salary": 45000, "is_active": True}
        return dict(row._mapping)
    finally:
        conn.close()


@router.post("/gosi-settings", dependencies=[Depends(require_permission("hr.manage"))])
def save_gosi_settings(data: GOSISettingsCreate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        # Deactivate old
        conn.execute(text("UPDATE gosi_settings SET is_active = FALSE"))
        result = conn.execute(text("""
            INSERT INTO gosi_settings (employee_share_percentage, employer_share_percentage, occupational_hazard_percentage, max_contributable_salary, effective_date)
            VALUES (:emp_pct, :empr_pct, :occ_pct, :max_sal, :eff_date) RETURNING id
        """), {
            "emp_pct": data.employee_share_percentage, "empr_pct": data.employer_share_percentage,
            "occ_pct": data.occupational_hazard_percentage, "max_sal": data.max_contributable_salary,
            "eff_date": data.effective_date or date.today()
        })
        conn.commit()
        return {"id": result.scalar(), "message": "تم حفظ إعدادات GOSI"}
    finally:
        conn.close()


@router.get("/gosi-calculation", response_model=List[GOSICalculationResponse], dependencies=[Depends(require_permission("hr.view"))])
def calculate_gosi(current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        # Get active settings
        settings = conn.execute(text("SELECT * FROM gosi_settings WHERE is_active = TRUE ORDER BY id DESC LIMIT 1")).fetchone()
        emp_pct = float(settings.employee_share_percentage) if settings else 9.75
        empr_pct = float(settings.employer_share_percentage) if settings else 11.75
        occ_pct = float(settings.occupational_hazard_percentage) if settings else 2.0
        max_sal = float(settings.max_contributable_salary) if settings else 45000

        employees = conn.execute(text("""
            SELECT id, first_name || ' ' || last_name as name, salary, housing_allowance
            FROM employees WHERE status = 'active'
        """)).fetchall()

        results = []
        for emp in employees:
            basic = float(emp.salary or 0)
            housing = float(emp.housing_allowance or 0)
            contributable = min(basic + housing, max_sal)
            emp_share = round(contributable * emp_pct / 100, 2)
            empr_share = round(contributable * empr_pct / 100, 2)
            occ_hazard = round(contributable * occ_pct / 100, 2)
            results.append({
                "employee_id": emp.id, "employee_name": emp.name,
                "basic_salary": basic, "housing_allowance": housing,
                "contributable_salary": contributable,
                "employee_share": emp_share, "employer_share": empr_share,
                "occupational_hazard": occ_hazard,
                "total_contribution": round(emp_share + empr_share + occ_hazard, 2)
            })
        return results
    finally:
        conn.close()


@router.get("/gosi-export", dependencies=[Depends(require_permission("hr.view"))])
def export_gosi(
    format: str = "excel",
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    تصدير ملف GOSI (التأمينات الاجتماعية) بتنسيق Excel أو PDF
    Export GOSI contribution file for submission to Saudi GOSI system
    """
    conn = get_db_connection(current_user.company_id)
    try:
        # Get active settings
        settings = conn.execute(text("SELECT * FROM gosi_settings WHERE is_active = TRUE ORDER BY id DESC LIMIT 1")).fetchone()
        emp_pct = float(settings.employee_share_percentage) if settings else 9.75
        empr_pct = float(settings.employer_share_percentage) if settings else 11.75
        occ_pct = float(settings.occupational_hazard_percentage) if settings else 2.0
        max_sal = float(settings.max_contributable_salary) if settings else 45000

        # Get employees with additional GOSI-relevant fields
        employees = conn.execute(text("""
            SELECT e.id, e.employee_number, e.first_name || ' ' || e.last_name as name,
                   e.salary, e.housing_allowance, e.national_id, e.nationality,
                   e.date_of_birth, e.hire_date, e.department
            FROM employees e
            WHERE e.status = 'active'
            ORDER BY e.department, e.first_name
        """)).fetchall()

        target_month = month or date.today().month
        target_year = year or date.today().year

        export_data = []
        total_emp_share = 0
        total_empr_share = 0
        total_occ_hazard = 0
        total_all = 0

        for emp in employees:
            basic = float(emp.salary or 0)
            housing = float(emp.housing_allowance or 0)
            contributable = min(basic + housing, max_sal)
            emp_share = round(contributable * emp_pct / 100, 2)
            empr_share = round(contributable * empr_pct / 100, 2)
            occ_hazard = round(contributable * occ_pct / 100, 2)
            total = round(emp_share + empr_share + occ_hazard, 2)

            total_emp_share += emp_share
            total_empr_share += empr_share
            total_occ_hazard += occ_hazard
            total_all += total

            export_data.append({
                "رقم الموظف / Emp #": getattr(emp, 'employee_number', '') or emp.id,
                "الاسم / Name": emp.name,
                "رقم الهوية / National ID": getattr(emp, 'national_id', '') or '',
                "الجنسية / Nationality": getattr(emp, 'nationality', '') or '',
                "القسم / Department": getattr(emp, 'department', '') or '',
                "الراتب الأساسي / Basic Salary": basic,
                "بدل السكن / Housing": housing,
                "الراتب الخاضع / Contributable": contributable,
                f"حصة الموظف {emp_pct}% / Employee Share": emp_share,
                f"حصة صاحب العمل {empr_pct}% / Employer Share": empr_share,
                f"أخطار مهنية {occ_pct}% / Occ. Hazard": occ_hazard,
                "الإجمالي / Total": total,
            })

        # Summary row
        export_data.append({
            "رقم الموظف / Emp #": "",
            "الاسم / Name": "الإجمالي / TOTAL",
            "رقم الهوية / National ID": "",
            "الجنسية / Nationality": "",
            "القسم / Department": "",
            "الراتب الأساسي / Basic Salary": "",
            "بدل السكن / Housing": "",
            "الراتب الخاضع / Contributable": "",
            f"حصة الموظف {emp_pct}% / Employee Share": round(total_emp_share, 2),
            f"حصة صاحب العمل {empr_pct}% / Employer Share": round(total_empr_share, 2),
            f"أخطار مهنية {occ_pct}% / Occ. Hazard": round(total_occ_hazard, 2),
            "الإجمالي / Total": round(total_all, 2),
        })

        columns = list(export_data[0].keys())
        period_str = f"{target_year}-{str(target_month).zfill(2)}"

        if format == "excel":
            buffer = generate_excel(export_data, columns, sheet_name=f"GOSI {period_str}")
            return create_export_response(buffer, f"gosi_report_{period_str}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        elif format == "csv":
            import csv, io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=columns)
            writer.writeheader()
            writer.writerows(export_data)
            csv_bytes = io.BytesIO(output.getvalue().encode('utf-8-sig'))
            return create_export_response(csv_bytes, f"gosi_report_{period_str}.csv", "text/csv")
        else:
            pdf_data = [columns]
            for row in export_data:
                pdf_data.append([str(row.get(c, '')) for c in columns])
            buffer = generate_pdf(pdf_data, f"GOSI Report - تقرير التأمينات الاجتماعية ({period_str})")
            return create_export_response(buffer, f"gosi_report_{period_str}.pdf", "application/pdf")
    finally:
        conn.close()


# =============================================
# مستندات الموظفين - Employee Documents
# =============================================

@router.get("/documents", response_model=List[EmployeeDocumentResponse], dependencies=[Depends(require_permission("hr.view"))])
def list_documents(employee_id: Optional[int] = None, expiring_soon: Optional[bool] = None, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT d.*, e.first_name || ' ' || e.last_name as employee_name
            FROM employee_documents d
            JOIN employees e ON d.employee_id = e.id
            WHERE 1=1
        """
        params = {}
        if employee_id:
            query += " AND d.employee_id = :eid"
            params["eid"] = employee_id
        if expiring_soon:
            query += " AND d.expiry_date IS NOT NULL AND d.expiry_date <= CURRENT_DATE + d.alert_days * INTERVAL '1 day'"
        query += " ORDER BY d.expiry_date ASC NULLS LAST"
        rows = conn.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/documents", dependencies=[Depends(require_permission("hr.manage"))])
def create_document(data: EmployeeDocumentCreate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        # Determine status based on expiry
        doc_status = "valid"
        if data.expiry_date:
            if data.expiry_date < date.today():
                doc_status = "expired"
            elif (data.expiry_date - date.today()).days <= data.alert_days:
                doc_status = "expiring_soon"

        result = conn.execute(text("""
            INSERT INTO employee_documents (employee_id, document_type, document_number, issue_date, expiry_date, issuing_authority, file_url, notes, alert_days, status)
            VALUES (:eid, :dtype, :dnum, :issue, :expiry, :auth, :url, :notes, :alert, :status) RETURNING id
        """), {
            "eid": data.employee_id, "dtype": data.document_type, "dnum": data.document_number,
            "issue": data.issue_date, "expiry": data.expiry_date, "auth": data.issuing_authority,
            "url": data.file_url, "notes": data.notes, "alert": data.alert_days, "status": doc_status
        })
        conn.commit()
        return {"id": result.scalar(), "message": "تم إضافة المستند"}
    finally:
        conn.close()


@router.put("/documents/{doc_id}", dependencies=[Depends(require_permission("hr.manage"))])
def update_document(doc_id: int, data: EmployeeDocumentUpdate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        fields, params = [], {"id": doc_id}
        for field in ["document_number", "issue_date", "expiry_date", "issuing_authority", "file_url", "notes", "alert_days"]:
            val = getattr(data, field, None)
            if val is not None:
                fields.append(f"{field} = :{field}")
                params[field] = val
        if not fields:
            raise HTTPException(status_code=400, detail="لا يوجد تعديلات")
        fields.append("updated_at = CURRENT_TIMESTAMP")
        conn.execute(text(f"UPDATE employee_documents SET {', '.join(fields)} WHERE id = :id"), params)
        conn.commit()
        return {"message": "تم التحديث"}
    finally:
        conn.close()


@router.delete("/documents/{doc_id}", dependencies=[Depends(require_permission("hr.manage"))])
def delete_document(doc_id: int, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        conn.execute(text("DELETE FROM employee_documents WHERE id = :id"), {"id": doc_id})
        conn.commit()
        return {"message": "تم الحذف"}
    finally:
        conn.close()


# =============================================
# تقييم الأداء - Performance Reviews
# =============================================

@router.get("/performance-reviews", response_model=List[PerformanceReviewResponse], dependencies=[Depends(require_permission("hr.view"))])
def list_performance_reviews(employee_id: Optional[int] = None, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT pr.*, 
                e.first_name || ' ' || e.last_name as employee_name,
                r.first_name || ' ' || r.last_name as reviewer_name
            FROM performance_reviews pr
            JOIN employees e ON pr.employee_id = e.id
            LEFT JOIN employees r ON pr.reviewer_id = r.id
            WHERE 1=1
        """
        params = {}
        if employee_id:
            query += " AND pr.employee_id = :eid"
            params["eid"] = employee_id
        query += " ORDER BY pr.review_date DESC"
        rows = conn.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/performance-reviews", dependencies=[Depends(require_permission("hr.manage"))])
def create_performance_review(data: PerformanceReviewCreate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        result = conn.execute(text("""
            INSERT INTO performance_reviews (employee_id, reviewer_id, review_period, review_date, review_type, overall_rating, strengths, weaknesses, goals)
            VALUES (:eid, :rid, :period, :rdate, :rtype, :rating, :strengths, :weaknesses, :goals) RETURNING id
        """), {
            "eid": data.employee_id, "rid": data.reviewer_id, "period": data.review_period,
            "rdate": data.review_date, "rtype": data.review_type, "rating": data.overall_rating,
            "strengths": data.strengths, "weaknesses": data.weaknesses, "goals": data.goals
        })
        conn.commit()
        return {"id": result.scalar(), "message": "تم إنشاء التقييم"}
    finally:
        conn.close()


@router.put("/performance-reviews/{review_id}", dependencies=[Depends(require_permission("hr.manage"))])
def update_performance_review(review_id: int, data: PerformanceReviewUpdate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        fields, params = [], {"id": review_id}
        for field in ["overall_rating", "strengths", "weaknesses", "goals", "self_rating", "self_comments", "manager_comments", "status"]:
            val = getattr(data, field, None)
            if val is not None:
                fields.append(f"{field} = :{field}")
                params[field] = val
        if not fields:
            raise HTTPException(status_code=400, detail="لا يوجد تعديلات")
        fields.append("updated_at = CURRENT_TIMESTAMP")
        conn.execute(text(f"UPDATE performance_reviews SET {', '.join(fields)} WHERE id = :id"), params)
        conn.commit()
        return {"message": "تم تحديث التقييم"}
    finally:
        conn.close()


# =============================================
# برامج التدريب - Training Programs
# =============================================

@router.get("/training", response_model=List[TrainingProgramResponse], dependencies=[Depends(require_permission("hr.view"))])
def list_training_programs(current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        rows = conn.execute(text("""
            SELECT t.*, COUNT(tp.id) as participant_count
            FROM training_programs t
            LEFT JOIN training_participants tp ON t.id = tp.training_id
            GROUP BY t.id
            ORDER BY t.start_date DESC NULLS LAST
        """)).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/training", dependencies=[Depends(require_permission("hr.manage"))])
def create_training_program(data: TrainingProgramCreate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        result = conn.execute(text("""
            INSERT INTO training_programs (name, name_en, description, trainer, location, start_date, end_date, max_participants, cost)
            VALUES (:name, :name_en, :desc, :trainer, :loc, :start, :end, :max, :cost) RETURNING id
        """), {
            "name": data.name, "name_en": data.name_en, "desc": data.description,
            "trainer": data.trainer, "loc": data.location, "start": data.start_date,
            "end": data.end_date, "max": data.max_participants, "cost": data.cost
        })
        conn.commit()
        return {"id": result.scalar(), "message": "تم إنشاء البرنامج التدريبي"}
    finally:
        conn.close()


@router.put("/training/{training_id}", dependencies=[Depends(require_permission("hr.manage"))])
def update_training_program(training_id: int, data: TrainingProgramUpdate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        fields, params = [], {"id": training_id}
        for field in ["name", "name_en", "description", "trainer", "location", "start_date", "end_date", "max_participants", "cost", "status"]:
            val = getattr(data, field, None)
            if val is not None:
                fields.append(f"{field} = :{field}")
                params[field] = val
        if not fields:
            raise HTTPException(status_code=400, detail="لا يوجد تعديلات")
        conn.execute(text(f"UPDATE training_programs SET {', '.join(fields)} WHERE id = :id"), params)
        conn.commit()
        return {"message": "تم التحديث"}
    finally:
        conn.close()


@router.post("/training/{training_id}/participants", dependencies=[Depends(require_permission("hr.manage"))])
def add_training_participant(training_id: int, data: TrainingParticipantCreate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        conn.execute(text("""
            INSERT INTO training_participants (training_id, employee_id)
            VALUES (:tid, :eid)
        """), {"tid": training_id, "eid": data.employee_id})
        conn.commit()
        return {"message": "تم تسجيل المشارك"}
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=400, detail="المشارك مسجل مسبقاً")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/training/{training_id}/participants", response_model=List[TrainingParticipantResponse], dependencies=[Depends(require_permission("hr.view"))])
def list_training_participants(training_id: int, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        rows = conn.execute(text("""
            SELECT tp.*, e.first_name || ' ' || e.last_name as employee_name
            FROM training_participants tp
            JOIN employees e ON tp.employee_id = e.id
            WHERE tp.training_id = :tid
            ORDER BY e.first_name
        """), {"tid": training_id}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.put("/training/participants/{participant_id}", dependencies=[Depends(require_permission("hr.manage"))])
def update_training_participant(participant_id: int, data: TrainingParticipantUpdate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        fields, params = [], {"id": participant_id}
        for field in ["attendance_status", "certificate_issued", "score", "feedback"]:
            val = getattr(data, field, None)
            if val is not None:
                fields.append(f"{field} = :{field}")
                params[field] = val
        if not fields:
            raise HTTPException(status_code=400, detail="لا يوجد تعديلات")
        conn.execute(text(f"UPDATE training_participants SET {', '.join(fields)} WHERE id = :id"), params)
        conn.commit()
        return {"message": "تم التحديث"}
    finally:
        conn.close()


# =============================================
# المخالفات - Violations
# =============================================

@router.get("/violations", response_model=List[ViolationResponse], dependencies=[Depends(require_permission("hr.view"))])
def list_violations(employee_id: Optional[int] = None, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT v.*, e.first_name || ' ' || e.last_name as employee_name
            FROM employee_violations v
            JOIN employees e ON v.employee_id = e.id
            WHERE 1=1
        """
        params = {}
        if employee_id:
            query += " AND v.employee_id = :eid"
            params["eid"] = employee_id
        query += " ORDER BY v.violation_date DESC"
        rows = conn.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/violations", dependencies=[Depends(require_permission("hr.manage"))])
def create_violation(data: ViolationCreate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get("id")
        result = conn.execute(text("""
            INSERT INTO employee_violations (employee_id, violation_date, violation_type, severity, description, action_taken, penalty_amount, deduct_from_salary, reported_by)
            VALUES (:eid, :vdate, :vtype, :sev, :desc, :action, :penalty, :deduct, :reported) RETURNING id
        """), {
            "eid": data.employee_id, "vdate": data.violation_date, "vtype": data.violation_type,
            "sev": data.severity, "desc": data.description, "action": data.action_taken,
            "penalty": data.penalty_amount, "deduct": data.deduct_from_salary,
            "reported": data.reported_by or user_id
        })
        conn.commit()
        return {"id": result.scalar(), "message": "تم تسجيل المخالفة"}
    finally:
        conn.close()


@router.put("/violations/{violation_id}", dependencies=[Depends(require_permission("hr.manage"))])
def update_violation(violation_id: int, data: ViolationUpdate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        fields, params = [], {"id": violation_id}
        for field in ["action_taken", "penalty_amount", "deduct_from_salary", "status"]:
            val = getattr(data, field, None)
            if val is not None:
                fields.append(f"{field} = :{field}")
                params[field] = val
        if not fields:
            raise HTTPException(status_code=400, detail="لا يوجد تعديلات")
        fields.append("updated_at = CURRENT_TIMESTAMP")
        conn.execute(text(f"UPDATE employee_violations SET {', '.join(fields)} WHERE id = :id"), params)
        conn.commit()
        return {"message": "تم تحديث المخالفة"}
    finally:
        conn.close()


# =============================================
# العهد - Employee Custody
# =============================================

@router.get("/custody", response_model=List[CustodyResponse], dependencies=[Depends(require_permission("hr.view"))])
def list_custody(employee_id: Optional[int] = None, status_filter: Optional[str] = None, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT c.*, e.first_name || ' ' || e.last_name as employee_name
            FROM employee_custody c
            JOIN employees e ON c.employee_id = e.id
            WHERE 1=1
        """
        params = {}
        if employee_id:
            query += " AND c.employee_id = :eid"
            params["eid"] = employee_id
        if status_filter:
            query += " AND c.status = :status"
            params["status"] = status_filter
        query += " ORDER BY c.assigned_date DESC"
        rows = conn.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/custody", dependencies=[Depends(require_permission("hr.manage"))])
def create_custody(data: CustodyCreate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        result = conn.execute(text("""
            INSERT INTO employee_custody (employee_id, item_name, item_type, serial_number, assigned_date, condition_on_assign, value, notes)
            VALUES (:eid, :item, :itype, :serial, :date, :condition, :value, :notes) RETURNING id
        """), {
            "eid": data.employee_id, "item": data.item_name, "itype": data.item_type,
            "serial": data.serial_number, "date": data.assigned_date,
            "condition": data.condition_on_assign, "value": data.value, "notes": data.notes
        })
        conn.commit()
        return {"id": result.scalar(), "message": "تم تسليم العهدة"}
    finally:
        conn.close()


@router.put("/custody/{custody_id}", dependencies=[Depends(require_permission("hr.manage"))])
def update_custody(custody_id: int, data: CustodyUpdate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        fields, params = [], {"id": custody_id}
        for field in ["return_date", "condition_on_return", "status", "notes"]:
            val = getattr(data, field, None)
            if val is not None:
                fields.append(f"{field} = :{field}")
                params[field] = val
        if not fields:
            raise HTTPException(status_code=400, detail="لا يوجد تعديلات")
        fields.append("updated_at = CURRENT_TIMESTAMP")
        conn.execute(text(f"UPDATE employee_custody SET {', '.join(fields)} WHERE id = :id"), params)
        conn.commit()
        return {"message": "تم تحديث العهدة"}
    finally:
        conn.close()


@router.put("/custody/{custody_id}/return", dependencies=[Depends(require_permission("hr.manage"))])
def return_custody(custody_id: int, data: CustodyUpdate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        conn.execute(text("""
            UPDATE employee_custody SET status = 'returned', return_date = CURRENT_DATE, 
            condition_on_return = :condition, notes = :notes, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """), {"condition": data.condition_on_return or "good", "notes": data.notes, "id": custody_id})
        conn.commit()
        return {"message": "تم استلام العهدة"}
    finally:
        conn.close()
