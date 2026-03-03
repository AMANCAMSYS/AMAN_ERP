/**
 * IndustryReport — صفحة عامة لتقارير النشاط المتخصصة
 * تعرض تقرير ديناميكي ببيانات حقيقية من backend endpoints مخصصة لكل تقرير
 */
import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import api from '../../services/apiClient'
import BackButton from '../../components/common/BackButton'
import { formatNumber } from '../../utils/format'

// ─── Report type metadata ───
const REPORT_CONFIG = {
  'food-cost': {
    icon: '🍽️', color: '#EF4444',
    titleAr: 'تقرير تكلفة الطعام', titleEn: 'Food Cost Report',
    descAr: 'نسبة تكلفة المواد الغذائية إلى الإيرادات', descEn: 'Food material cost vs revenue ratio',
    endpoint: '/reports/industry/food-cost',
  },
  'production-cost': {
    icon: '🏭', color: '#6366f1',
    titleAr: 'تقرير تكلفة الإنتاج', titleEn: 'Production Cost Report',
    descAr: 'مقارنة التكلفة المخططة بالفعلية للإنتاج', descEn: 'Planned vs actual production cost',
    endpoint: '/reports/industry/production-cost',
  },
  'progress-billing': {
    icon: '🏗️', color: '#F59E0B',
    titleAr: 'مستخلصات المشاريع', titleEn: 'Progress Billing Report',
    descAr: 'نسبة الإنجاز والفواتير لكل مشروع', descEn: 'Project completion & billing progress',
    endpoint: '/reports/industry/progress-billing',
  },
  'utilization': {
    icon: '💼', color: '#8B5CF6',
    titleAr: 'معدل الاستغلال', titleEn: 'Utilization Report',
    descAr: 'ساعات العمل المفوترة مقابل المتاحة', descEn: 'Billable vs available hours',
    endpoint: '/reports/industry/utilization',
  },
  'drug-expiry': {
    icon: '💊', color: '#10B981',
    titleAr: 'صلاحية الأدوية والمنتجات', titleEn: 'Drug/Product Expiry Report',
    descAr: 'المنتجات قريبة الانتهاء أو المنتهية', descEn: 'Products expiring or already expired',
    endpoint: '/reports/industry/drug-expiry',
  },
  'workshop-revenue': {
    icon: '🔧', color: '#6B7280',
    titleAr: 'إيرادات الورشة', titleEn: 'Workshop Revenue Report',
    descAr: 'الإيرادات مقسومة حسب نوع الخدمة وقطع الغيار', descEn: 'Revenue breakdown by service type',
    endpoint: '/reports/industry/workshop-revenue',
  },
  'ecom-returns': {
    icon: '🛒', color: '#3B82F6',
    titleAr: 'تقرير المرتجعات', titleEn: 'Returns Analysis Report',
    descAr: 'نسبة المرتجعات وأكثر المنتجات ارتجاعاً', descEn: 'Return rates and top returned products',
    endpoint: '/reports/industry/ecom-returns',
  },
  'agent-performance': {
    icon: '📦', color: '#0EA5E9',
    titleAr: 'أداء الوكلاء والمناديب', titleEn: 'Agent Performance Report',
    descAr: 'مبيعات كل مندوب ونسبة التحصيل', descEn: 'Sales per agent and collection rate',
    endpoint: '/reports/industry/agent-performance',
  },
  'fleet-tracking': {
    icon: '🚛', color: '#14B8A6',
    titleAr: 'كفاءة الأسطول', titleEn: 'Fleet Efficiency Report',
    descAr: 'أداء التوصيل والمركبات', descEn: 'Delivery performance & vehicle tracking',
    endpoint: '/reports/industry/fleet-tracking',
  },
  'crop-yield': {
    icon: '🌾', color: '#65A30D',
    titleAr: 'إنتاجية المحاصيل', titleEn: 'Crop Yield Report',
    descAr: 'عوائد المنتجات الزراعية مقابل التكاليف', descEn: 'Crop revenue vs farming costs',
    endpoint: '/reports/industry/crop-yield',
  },
}

// ─── Formatting helpers ───
const fmtNum  = (n) => formatNumber ? formatNumber(n) : Number(n || 0).toLocaleString('en-US', { maximumFractionDigits: 2 })
const fmtPct  = (n) => `${Number(n || 0).toFixed(1)}%`
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-CA') : '—'

// ─── Metric card ───
function MetricCard({ label, value, sub, color, alert }) {
  return (
    <div className="metric-card" style={{ borderTop: `3px solid ${color}`, position: 'relative' }}>
      {alert && <span style={{ position: 'absolute', top: 8, insetInlineEnd: 8, fontSize: 18 }}>{alert}</span>}
      <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700 }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

// ─── Table renderer ───
function DataTable({ columns, rows, color }) {
  if (!rows?.length) return null
  return (
    <div className="table-responsive" style={{ marginTop: 8 }}>
      <table className="data-table" style={{ width: '100%' }}>
        <thead>
          <tr>{columns.map((c, i) => <th key={i} style={c.align ? { textAlign: c.align } : {}}>{c.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri}>
              {columns.map((c, ci) => (
                <td key={ci} style={c.align ? { textAlign: c.align } : {}}>
                  {c.render ? c.render(row) : (row[c.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ═══════════════════════════════════════════
//   RENDER FUNCTIONS PER REPORT TYPE
// ═══════════════════════════════════════════

function renderFoodCost(data, isRTL, color) {
  const s = data.summary || {}
  return <>
    <div className="metrics-grid">
      <MetricCard color={color} label={isRTL ? 'الإيرادات' : 'Revenue'} value={fmtNum(s.revenue)} />
      <MetricCard color={color} label={isRTL ? 'تكلفة البضاعة' : 'COGS'} value={fmtNum(s.cogs)} />
      <MetricCard color="#EF4444" label={isRTL ? 'نسبة تكلفة الطعام' : 'Food Cost %'}
        value={fmtPct(s.food_cost_pct)} alert={s.food_cost_pct > 35 ? '⚠️' : '✅'}
        sub={s.food_cost_pct > 35 ? (isRTL ? 'أعلى من المعيار (35%)' : 'Above benchmark (35%)') : (isRTL ? 'ضمن المعيار' : 'Within benchmark')} />
      <MetricCard color="#10B981" label={isRTL ? 'هامش الربح الإجمالي' : 'Gross Margin'} value={fmtPct(s.gross_margin_pct)} />
      <MetricCard color={color} label={isRTL ? 'الربح الإجمالي' : 'Gross Profit'} value={fmtNum(s.gross_profit)} />
      <MetricCard color={color} label={isRTL ? 'صافي الربح' : 'Net Profit'} value={fmtNum(s.net_profit)} />
    </div>
    {data.top_items?.length > 0 && (
      <div className="card" style={{ padding: 20, marginTop: 16 }}>
        <h3>📊 {isRTL ? 'أعلى 10 منتجات مبيعاً' : 'Top 10 Selling Items'}</h3>
        <DataTable color={color} rows={data.top_items} columns={[
          { key: 'product_name', label: isRTL ? 'المنتج' : 'Product' },
          { key: 'qty_sold', label: isRTL ? 'الكمية' : 'Qty', align: 'center', render: r => fmtNum(r.qty_sold) },
          { key: 'total_revenue', label: isRTL ? 'الإيراد' : 'Revenue', align: 'right', render: r => fmtNum(r.total_revenue) },
          { key: 'total_cost', label: isRTL ? 'التكلفة' : 'Cost', align: 'right', render: r => fmtNum(r.total_cost) },
          { key: 'cost_pct', label: isRTL ? 'نسبة التكلفة' : 'Cost %', align: 'center', render: r => <span style={{ color: r.cost_pct > 35 ? '#EF4444' : '#10B981', fontWeight: 600 }}>{fmtPct(r.cost_pct)}</span> },
        ]} />
      </div>
    )}
  </>
}

function renderProductionCost(data, isRTL, color) {
  const s = data.summary || {}
  return <>
    <div className="metrics-grid">
      <MetricCard color={color} label={isRTL ? 'أوامر الإنتاج' : 'Production Orders'} value={s.total_orders} />
      <MetricCard color={color} label={isRTL ? 'المنتج' : 'Produced'} value={fmtNum(s.produced_qty)} sub={`${isRTL ? 'مخطط' : 'Planned'}: ${fmtNum(s.planned_qty)}`} />
      <MetricCard color="#10B981" label={isRTL ? 'كفاءة الإنتاج' : 'Efficiency'} value={fmtPct(s.efficiency_pct)} />
      <MetricCard color="#EF4444" label={isRTL ? 'نسبة الهالك' : 'Scrap Rate'} value={fmtPct(s.scrap_rate_pct)} alert={s.scrap_rate_pct > 5 ? '⚠️' : ''} />
      <MetricCard color={color} label={isRTL ? 'التكلفة المخططة' : 'Planned Cost'} value={fmtNum(s.planned_cost)} />
      <MetricCard color={color} label={isRTL ? 'التكلفة الفعلية' : 'Actual Cost'} value={fmtNum(s.total_actual_cost)} />
      <MetricCard color={s.variance > 0 ? '#EF4444' : '#10B981'} label={isRTL ? 'الانحراف' : 'Variance'}
        value={fmtNum(s.variance)} sub={`${fmtPct(s.variance_pct)} ${s.variance > 0 ? (isRTL ? 'تجاوز' : 'over') : (isRTL ? 'وفر' : 'under')}`} />
    </div>
    {data.orders?.length > 0 && (
      <div className="card" style={{ padding: 20, marginTop: 16 }}>
        <h3>🏭 {isRTL ? 'أوامر الإنتاج' : 'Production Orders'}</h3>
        <DataTable color={color} rows={data.orders} columns={[
          { key: 'order_number', label: '#' },
          { key: 'product_name', label: isRTL ? 'المنتج' : 'Product' },
          { key: 'status', label: isRTL ? 'الحالة' : 'Status' },
          { key: 'planned_qty', label: isRTL ? 'مخطط' : 'Planned', align: 'center', render: r => fmtNum(r.planned_qty) },
          { key: 'produced_quantity', label: isRTL ? 'منتج' : 'Produced', align: 'center', render: r => fmtNum(r.produced_quantity) },
          { key: 'scrapped_quantity', label: isRTL ? 'هالك' : 'Scrapped', align: 'center', render: r => fmtNum(r.scrapped_quantity) },
        ]} />
      </div>
    )}
  </>
}

function renderProgressBilling(data, isRTL, color) {
  const s = data.summary || {}
  return <>
    <div className="metrics-grid">
      <MetricCard color={color} label={isRTL ? 'المشاريع' : 'Projects'} value={s.total_projects} sub={`${s.active_projects || 0} ${isRTL ? 'نشط' : 'active'}`} />
      <MetricCard color={color} label={isRTL ? 'إجمالي الميزانيات' : 'Total Budgets'} value={fmtNum(s.total_budget)} />
      <MetricCard color="#10B981" label={isRTL ? 'إجمالي المفوتر' : 'Total Invoiced'} value={fmtNum(s.total_invoiced)} sub={fmtPct(s.overall_billing_pct)} />
      <MetricCard color={color} label={isRTL ? 'إجمالي التكاليف' : 'Total Costs'} value={fmtNum(s.total_cost)} />
      <MetricCard color={s.overall_profit >= 0 ? '#10B981' : '#EF4444'} label={isRTL ? 'الربح الإجمالي' : 'Overall Profit'} value={fmtNum(s.overall_profit)} />
    </div>
    {data.projects?.length > 0 && (
      <div className="card" style={{ padding: 20, marginTop: 16 }}>
        <h3>📋 {isRTL ? 'تفاصيل المشاريع' : 'Project Details'}</h3>
        <DataTable color={color} rows={data.projects} columns={[
          { key: 'project_code', label: '#' },
          { key: 'project_name', label: isRTL ? 'المشروع' : 'Project' },
          { key: 'status', label: isRTL ? 'الحالة' : 'Status' },
          { key: 'progress_percentage', label: isRTL ? 'الإنجاز' : 'Progress', align: 'center',
            render: r => (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ flex: 1, height: 6, background: '#e2e8f0', borderRadius: 3 }}>
                  <div style={{ width: `${r.progress_percentage || 0}%`, height: '100%', background: color, borderRadius: 3 }} />
                </div>
                <span style={{ fontSize: 11, minWidth: 35 }}>{fmtPct(r.progress_percentage)}</span>
              </div>
            )
          },
          { key: 'planned_budget', label: isRTL ? 'الميزانية' : 'Budget', align: 'right', render: r => fmtNum(r.planned_budget) },
          { key: 'invoiced_amount', label: isRTL ? 'المفوتر' : 'Invoiced', align: 'right', render: r => fmtNum(r.invoiced_amount) },
          { key: 'profit', label: isRTL ? 'الربح' : 'Profit', align: 'right', render: r => <span style={{ color: r.profit >= 0 ? '#10B981' : '#EF4444' }}>{fmtNum(r.profit)}</span> },
        ]} />
      </div>
    )}
  </>
}

function renderDrugExpiry(data, isRTL, color) {
  const s = data.summary || {}
  return <>
    <div className="metrics-grid">
      <MetricCard color="#EF4444" label={isRTL ? 'منتهية الصلاحية' : 'Expired'} value={s.expired_count} alert={s.expired_count > 0 ? '🔴' : ''} />
      <MetricCard color="#F59E0B" label={isRTL ? 'خلال 30 يوم' : 'Expires in 30d'} value={s.expiring_30_days} alert={s.expiring_30_days > 0 ? '🟡' : ''} />
      <MetricCard color="#3B82F6" label={isRTL ? 'خلال 60 يوم' : 'Expires in 60d'} value={s.expiring_60_days} />
      <MetricCard color="#10B981" label={isRTL ? 'خلال 90 يوم' : 'Expires in 90d'} value={s.expiring_90_days} />
      <MetricCard color="#EF4444" label={isRTL ? 'القيمة المعرضة للخطر' : 'Value at Risk'} value={fmtNum(s.total_value_at_risk)} />
    </div>
    {data.items?.length > 0 && (
      <div className="card" style={{ padding: 20, marginTop: 16 }}>
        <h3>💊 {isRTL ? 'المنتجات المعرضة للخطر' : 'At-Risk Products'}</h3>
        <DataTable color={color} rows={data.items} columns={[
          { key: 'product_name', label: isRTL ? 'المنتج' : 'Product' },
          { key: 'batch_number', label: isRTL ? 'رقم الدفعة' : 'Batch #' },
          { key: 'warehouse_name', label: isRTL ? 'المستودع' : 'Warehouse' },
          { key: 'available_quantity', label: isRTL ? 'الكمية' : 'Qty', align: 'center', render: r => fmtNum(r.available_quantity) },
          { key: 'expiry_date', label: isRTL ? 'الانتهاء' : 'Expiry', render: r => fmtDate(r.expiry_date) },
          { key: 'days_left', label: isRTL ? 'المتبقي' : 'Days Left', align: 'center',
            render: r => <span style={{ fontWeight: 700, color: r.days_left <= 0 ? '#EF4444' : r.days_left <= 30 ? '#F59E0B' : '#10B981' }}>{r.days_left}</span> },
          { key: 'value_at_risk', label: isRTL ? 'القيمة' : 'Value', align: 'right', render: r => fmtNum(r.value_at_risk) },
        ]} />
      </div>
    )}
  </>
}

function renderFleetTracking(data, isRTL, color) {
  const s = data.summary || {}
  return <>
    <div className="metrics-grid">
      <MetricCard color={color} label={isRTL ? 'إجمالي التوصيلات' : 'Total Deliveries'} value={s.total} />
      <MetricCard color="#10B981" label={isRTL ? 'تم التسليم' : 'Delivered'} value={s.delivered} />
      <MetricCard color="#F59E0B" label={isRTL ? 'في الطريق' : 'In Transit'} value={s.in_transit} />
      <MetricCard color="#EF4444" label={isRTL ? 'ملغاة' : 'Cancelled'} value={s.cancelled} />
      <MetricCard color={color} label={isRTL ? 'المركبات' : 'Vehicles'} value={s.vehicles_used} />
      <MetricCard color={color} label={isRTL ? 'نسبة الإنجاز' : 'Completion Rate'} value={fmtPct(s.on_time_rate)} />
    </div>
    {data.vehicles?.length > 0 && (
      <div className="card" style={{ padding: 20, marginTop: 16 }}>
        <h3>🚛 {isRTL ? 'أداء المركبات' : 'Vehicle Performance'}</h3>
        <DataTable color={color} rows={data.vehicles} columns={[
          { key: 'vehicle_number', label: isRTL ? 'المركبة' : 'Vehicle' },
          { key: 'driver_name', label: isRTL ? 'السائق' : 'Driver' },
          { key: 'total_deliveries', label: isRTL ? 'الرحلات' : 'Trips', align: 'center' },
          { key: 'completed', label: isRTL ? 'مكتمل' : 'Done', align: 'center' },
          { key: 'completion_rate', label: isRTL ? 'نسبة الإنجاز' : 'Rate', align: 'center', render: r => fmtPct(r.completion_rate) },
          { key: 'total_qty', label: isRTL ? 'الكمية' : 'Qty', align: 'right', render: r => fmtNum(r.total_qty) },
        ]} />
      </div>
    )}
  </>
}

function renderUtilization(data, isRTL, color) {
  const s = data.summary || {}
  return <>
    <div className="metrics-grid">
      <MetricCard color={color} label={isRTL ? 'الموظفون' : 'Employees'} value={s.total_employees} />
      <MetricCard color={color} label={isRTL ? 'ساعات مفوترة' : 'Billable Hours'} value={fmtNum(s.total_billable_hours)} />
      <MetricCard color={s.avg_utilization_pct >= 70 ? '#10B981' : '#F59E0B'} label={isRTL ? 'معدل الاستغلال' : 'Avg Utilization'}
        value={fmtPct(s.avg_utilization_pct)} alert={s.avg_utilization_pct >= 70 ? '✅' : '⚠️'} />
      <MetricCard color={color} label={isRTL ? 'سعر الساعة الفعلي' : 'Eff. Hourly Rate'} value={fmtNum(s.effective_hourly_rate)} />
      <MetricCard color={color} label={isRTL ? 'إيراد الخدمات' : 'Service Revenue'} value={fmtNum(s.service_revenue)} />
      <MetricCard color={s.net_profit >= 0 ? '#10B981' : '#EF4444'} label={isRTL ? 'صافي الربح' : 'Net Profit'} value={fmtNum(s.net_profit)} />
    </div>
    {data.employees?.length > 0 && (
      <div className="card" style={{ padding: 20, marginTop: 16 }}>
        <h3>👥 {isRTL ? 'أداء الموظفين' : 'Employee Performance'}</h3>
        <DataTable color={color} rows={data.employees} columns={[
          { key: 'employee_name', label: isRTL ? 'الموظف' : 'Employee' },
          { key: 'billable_hours', label: isRTL ? 'ساعات مفوترة' : 'Billable', align: 'center', render: r => fmtNum(r.billable_hours) },
          { key: 'available_hours', label: isRTL ? 'متاحة' : 'Available', align: 'center' },
          { key: 'utilization_pct', label: isRTL ? 'الاستغلال' : 'Util %', align: 'center',
            render: r => <span style={{ fontWeight: 600, color: r.utilization_pct >= 70 ? '#10B981' : '#F59E0B' }}>{fmtPct(r.utilization_pct)}</span> },
          { key: 'tasks_count', label: isRTL ? 'المهام' : 'Tasks', align: 'center' },
          { key: 'completed_tasks', label: isRTL ? 'مكتمل' : 'Done', align: 'center' },
        ]} />
      </div>
    )}
  </>
}

function renderWorkshopRevenue(data, isRTL, color) {
  const s = data.summary || {}
  return <>
    <div className="metrics-grid">
      <MetricCard color={color} label={isRTL ? 'عدد الأعمال' : 'Total Jobs'} value={s.total_jobs} />
      <MetricCard color={color} label={isRTL ? 'الإيرادات' : 'Revenue'} value={fmtNum(s.total_revenue)} />
      <MetricCard color={color} label={isRTL ? 'متوسط قيمة العمل' : 'Avg Job Value'} value={fmtNum(s.avg_job_value)} />
      <MetricCard color="#10B981" label={isRTL ? 'هامش الربح' : 'Gross Margin'} value={fmtPct(s.gross_margin_pct)} />
      <MetricCard color={color} label={isRTL ? 'خدمات' : 'Services'} value={s.service_items} />
      <MetricCard color={color} label={isRTL ? 'قطع غيار' : 'Parts'} value={s.parts_items} />
    </div>
    {data.services?.length > 0 && (
      <div className="card" style={{ padding: 20, marginTop: 16 }}>
        <h3>🔧 {isRTL ? 'تفاصيل الخدمات' : 'Service Breakdown'}</h3>
        <DataTable color={color} rows={data.services} columns={[
          { key: 'service_name', label: isRTL ? 'الخدمة/القطعة' : 'Service/Part' },
          { key: 'product_type', label: isRTL ? 'النوع' : 'Type', render: r => r.product_type === 'service' ? (isRTL ? 'خدمة' : 'Service') : (isRTL ? 'منتج' : 'Part') },
          { key: 'job_count', label: isRTL ? 'العدد' : 'Jobs', align: 'center' },
          { key: 'total_revenue', label: isRTL ? 'الإيراد' : 'Revenue', align: 'right', render: r => fmtNum(r.total_revenue) },
          { key: 'margin', label: isRTL ? 'الربح' : 'Margin', align: 'right', render: r => fmtNum(r.margin) },
          { key: 'margin_pct', label: '%', align: 'center', render: r => <span style={{ color: r.margin_pct >= 30 ? '#10B981' : '#EF4444' }}>{fmtPct(r.margin_pct)}</span> },
        ]} />
      </div>
    )}
  </>
}

function renderEcomReturns(data, isRTL, color) {
  const s = data.summary || {}
  return <>
    <div className="metrics-grid">
      <MetricCard color={color} label={isRTL ? 'إجمالي المبيعات' : 'Total Sales'} value={s.total_sales} sub={fmtNum(s.total_sales_value)} />
      <MetricCard color="#EF4444" label={isRTL ? 'المرتجعات' : 'Returns'} value={s.total_returns} sub={fmtNum(s.total_return_value)} />
      <MetricCard color={s.return_rate_pct > 10 ? '#EF4444' : '#10B981'} label={isRTL ? 'نسبة الإرجاع (عدد)' : 'Return Rate (count)'}
        value={fmtPct(s.return_rate_pct)} alert={s.return_rate_pct > 10 ? '⚠️' : '✅'} />
      <MetricCard color={color} label={isRTL ? 'نسبة الإرجاع (قيمة)' : 'Return Rate (value)'} value={fmtPct(s.value_return_rate_pct)} />
      <MetricCard color="#10B981" label={isRTL ? 'صافي المبيعات' : 'Net Sales'} value={fmtNum(s.net_sales)} />
    </div>
    {data.top_returned_products?.length > 0 && (
      <div className="card" style={{ padding: 20, marginTop: 16 }}>
        <h3>📦 {isRTL ? 'أكثر المنتجات مرتجعاً' : 'Top Returned Products'}</h3>
        <DataTable color={color} rows={data.top_returned_products} columns={[
          { key: 'product_name', label: isRTL ? 'المنتج' : 'Product' },
          { key: 'product_code', label: isRTL ? 'الكود' : 'Code' },
          { key: 'return_count', label: isRTL ? 'عدد المرتجعات' : 'Returns', align: 'center' },
          { key: 'returned_qty', label: isRTL ? 'الكمية' : 'Qty', align: 'center', render: r => fmtNum(r.returned_qty) },
          { key: 'return_value', label: isRTL ? 'القيمة' : 'Value', align: 'right', render: r => fmtNum(r.return_value) },
        ]} />
      </div>
    )}
  </>
}

function renderAgentPerformance(data, isRTL, color) {
  const s = data.summary || {}
  return <>
    <div className="metrics-grid">
      <MetricCard color={color} label={isRTL ? 'عدد المناديب' : 'Total Agents'} value={s.total_agents} />
      <MetricCard color={color} label={isRTL ? 'إجمالي المبيعات' : 'Grand Total'} value={fmtNum(s.grand_total_sales)} />
      <MetricCard color={color} label={isRTL ? 'متوسط لكل مندوب' : 'Avg per Agent'} value={fmtNum(s.avg_sales_per_agent)} />
    </div>
    {data.agents?.length > 0 && (
      <div className="card" style={{ padding: 20, marginTop: 16 }}>
        <h3>👤 {isRTL ? 'أداء المناديب' : 'Agent Breakdown'}</h3>
        <DataTable color={color} rows={data.agents} columns={[
          { key: 'agent_full_name', label: isRTL ? 'المندوب' : 'Agent', render: r => r.agent_full_name || r.agent_name },
          { key: 'invoice_count', label: isRTL ? 'الفواتير' : 'Invoices', align: 'center' },
          { key: 'total_sales', label: isRTL ? 'المبيعات' : 'Sales', align: 'right', render: r => fmtNum(r.total_sales) },
          { key: 'total_collected', label: isRTL ? 'المحصّل' : 'Collected', align: 'right', render: r => fmtNum(r.total_collected) },
          { key: 'collection_rate_pct', label: isRTL ? 'التحصيل' : 'Collection', align: 'center',
            render: r => <span style={{ color: r.collection_rate_pct >= 80 ? '#10B981' : '#EF4444' }}>{fmtPct(r.collection_rate_pct)}</span> },
          { key: 'customer_count', label: isRTL ? 'العملاء' : 'Customers', align: 'center' },
          { key: 'share_pct', label: isRTL ? 'الحصة' : 'Share', align: 'center', render: r => fmtPct(r.share_pct) },
        ]} />
      </div>
    )}
    {data.top_customers?.length > 0 && (
      <div className="card" style={{ padding: 20, marginTop: 16 }}>
        <h3>🏆 {isRTL ? 'أكبر العملاء' : 'Top Customers'}</h3>
        <DataTable color={color} rows={data.top_customers} columns={[
          { key: 'customer_name', label: isRTL ? 'العميل' : 'Customer' },
          { key: 'order_count', label: isRTL ? 'الطلبات' : 'Orders', align: 'center' },
          { key: 'total_value', label: isRTL ? 'القيمة' : 'Value', align: 'right', render: r => fmtNum(r.total_value) },
        ]} />
      </div>
    )}
  </>
}

function renderCropYield(data, isRTL, color) {
  const s = data.summary || {}
  return <>
    <div className="metrics-grid">
      <MetricCard color={color} label={isRTL ? 'المحاصيل' : 'Crops'} value={s.total_crops} />
      <MetricCard color={color} label={isRTL ? 'الإيرادات' : 'Revenue'} value={fmtNum(s.total_revenue)} />
      <MetricCard color={color} label={isRTL ? 'التكلفة المباشرة' : 'Direct Cost'} value={fmtNum(s.total_direct_cost)} />
      <MetricCard color="#10B981" label={isRTL ? 'هامش الربح' : 'Gross Margin'} value={fmtPct(s.gross_margin_pct)} />
      <MetricCard color={color} label={isRTL ? 'مصاريف التشغيل' : 'Operating Exp.'} value={fmtNum(s.total_operating_expenses)} />
      <MetricCard color={s.net_farm_income >= 0 ? '#10B981' : '#EF4444'} label={isRTL ? 'صافي دخل المزرعة' : 'Net Farm Income'} value={fmtNum(s.net_farm_income)} />
    </div>
    {data.crops?.length > 0 && (
      <div className="card" style={{ padding: 20, marginTop: 16 }}>
        <h3>🌾 {isRTL ? 'تفاصيل المحاصيل' : 'Crop Details'}</h3>
        <DataTable color={color} rows={data.crops} columns={[
          { key: 'product_name', label: isRTL ? 'المحصول' : 'Crop' },
          { key: 'total_qty_sold', label: isRTL ? 'الكمية' : 'Qty', align: 'center', render: r => fmtNum(r.total_qty_sold) },
          { key: 'total_revenue', label: isRTL ? 'الإيراد' : 'Revenue', align: 'right', render: r => fmtNum(r.total_revenue) },
          { key: 'total_cost', label: isRTL ? 'التكلفة' : 'Cost', align: 'right', render: r => fmtNum(r.total_cost) },
          { key: 'profit', label: isRTL ? 'الربح' : 'Profit', align: 'right', render: r => <span style={{ color: r.profit >= 0 ? '#10B981' : '#EF4444' }}>{fmtNum(r.profit)}</span> },
          { key: 'margin_pct', label: '%', align: 'center', render: r => fmtPct(r.margin_pct) },
        ]} />
      </div>
    )}
  </>
}

// ─── RENDERER MAP ───
const RENDERERS = {
  'food-cost': renderFoodCost,
  'production-cost': renderProductionCost,
  'progress-billing': renderProgressBilling,
  'drug-expiry': renderDrugExpiry,
  'fleet-tracking': renderFleetTracking,
  'utilization': renderUtilization,
  'workshop-revenue': renderWorkshopRevenue,
  'ecom-returns': renderEcomReturns,
  'agent-performance': renderAgentPerformance,
  'crop-yield': renderCropYield,
}

// ═══════════════════════════════════════════
//   MAIN COMPONENT
// ═══════════════════════════════════════════
export default function IndustryReport() {
  const { reportType } = useParams()
  const { i18n } = useTranslation()
  const isRTL = i18n.language === 'ar'

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const config = REPORT_CONFIG[reportType]

  useEffect(() => {
    if (!config) { setError('Unknown report type'); setLoading(false); return }
    fetchReport()
  }, [reportType])

  const fetchReport = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await api.get(config.endpoint)
      setData(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load report')
    } finally {
      setLoading(false)
    }
  }

  if (!config) {
    return (
      <div className="workspace fade-in">
        <div className="workspace-header"><BackButton /><h1>❌ {isRTL ? 'غير موجود' : 'Not Found'}</h1></div>
        <p>{isRTL ? 'هذا التقرير غير موجود.' : 'This report type does not exist.'}</p>
      </div>
    )
  }

  const title = isRTL ? config.titleAr : config.titleEn
  const desc  = isRTL ? config.descAr  : config.descEn
  const renderFn = RENDERERS[reportType]

  return (
    <div className="workspace fade-in">
      <div className="workspace-header">
        <BackButton />
        <div className="header-title">
          <h1 className="workspace-title">
            <span style={{ marginInlineEnd: 8 }}>{config.icon}</span>{title}
          </h1>
          <p className="workspace-subtitle">{desc}</p>
        </div>
      </div>

      {data?.period && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 16, fontSize: 13, color: '#64748b' }}>
          <span>📅 {data.period.from} → {data.period.to}</span>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <div className="spinner" style={{
            width: 40, height: 40, border: '3px solid #e2e8f0',
            borderTopColor: config.color, borderRadius: '50%',
            animation: 'spin 0.8s linear infinite', margin: '0 auto 16px',
          }} />
          <p style={{ color: '#64748b' }}>{isRTL ? 'جاري التحميل...' : 'Loading...'}</p>
        </div>
      ) : error ? (
        <div className="card" style={{ padding: 40, textAlign: 'center' }}>
          <p style={{ color: '#EF4444', fontSize: 16, marginBottom: 12 }}>❌ {error}</p>
          <button onClick={fetchReport} className="btn btn-primary" style={{ padding: '8px 20px' }}>
            {isRTL ? 'إعادة المحاولة' : 'Retry'}
          </button>
        </div>
      ) : data && renderFn ? (
        <div style={{ display: 'grid', gap: 16 }}>
          {renderFn(data, isRTL, config.color)}
        </div>
      ) : (
        <div className="card" style={{ padding: 40, textAlign: 'center', color: '#94a3b8' }}>
          {isRTL ? 'لا توجد بيانات لهذه الفترة' : 'No data for this period'}
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
