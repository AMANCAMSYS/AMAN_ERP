/**
 * مصفوفة الوحدات حسب نوع النشاط التجاري
 * Industry Modules Matrix — AMAN ERP
 * 
 * 17 وحدة ثابتة تظهر في جميع الأنشطة
 * 5 وحدات متغيرة تتغير حسب النشاط
 */

// ===== الوحدات الثابتة (تظهر دائماً في كل الأنشطة) =====
export const ALWAYS_ENABLED_MODULES = [
  'dashboard',
  'kpi',
  'accounting',
  'assets',
  'treasury',
  'sales',
  'buying',
  'crm',
  'expenses',
  'taxes',
  'approvals',
  'reports',
  'hr',
  'audit',
  'roles',
  'settings',
  'data_import',
]

// ===== الوحدات المتغيرة حسب النشاط =====
export const VARIABLE_MODULES = ['pos', 'stock', 'manufacturing', 'projects', 'services']

// ===== تحويل بين Key و Code =====
// Key = رمز قصير (RT, FB, MF) — يُستخدم في الفرونت كمعرف، و localStorage
// Code = اسم نصي (retail, restaurant, manufacturing) — يُخزّن في الباك اند
export const KEY_TO_CODE = {}
export const CODE_TO_KEY = {}

// Will be populated after INDUSTRY_TYPES is defined (see bottom of file)

// ===== أنواع الأنشطة الـ 12 =====
export const INDUSTRY_TYPES = {
  RT: {
    key: 'RT',
    code: 'retail',
    nameAr: 'تجارة التجزئة',
    nameEn: 'Retail',
    icon: '🛍️',
    descriptionAr: 'بقالات، ملابس، إلكترونيات، عطور، هدايا',
    descriptionEn: 'Grocery, clothing, electronics, perfumes, gifts',
    variableModules: {
      pos: true,
      stock: true,
      manufacturing: false,
      projects: false,
      services: false,
    },
  },
  WS: {
    key: 'WS',
    code: 'wholesale',
    nameAr: 'الجملة والتوزيع',
    nameEn: 'Wholesale & Distribution',
    icon: '📦',
    descriptionAr: 'موزعين، مستودعات جملة، وكلاء بيع، مستوردين',
    descriptionEn: 'Distributors, wholesale warehouses, agents, importers',
    variableModules: {
      pos: false,
      stock: true,
      manufacturing: false,
      projects: false,
      services: false,
    },
  },
  FB: {
    key: 'FB',
    code: 'restaurant',
    nameAr: 'المطاعم والمقاهي',
    nameEn: 'Food & Beverage',
    icon: '🍽️',
    descriptionAr: 'مطاعم، كافيهات، مطابخ سحابية، فود ترك، مخابز',
    descriptionEn: 'Restaurants, cafés, cloud kitchens, food trucks, bakeries',
    variableModules: {
      pos: true,
      stock: true,
      manufacturing: false,
      projects: false,
      services: false,
    },
  },
  MF: {
    key: 'MF',
    code: 'manufacturing',
    nameAr: 'التصنيع والإنتاج',
    nameEn: 'Manufacturing',
    icon: '🏭',
    descriptionAr: 'مصانع، ورش إنتاج، تعبئة وتغليف، نجارة صناعية',
    descriptionEn: 'Factories, production workshops, packaging, industrial',
    variableModules: {
      pos: false,
      stock: true,
      manufacturing: true,
      projects: true,
      services: true,
    },
  },
  CN: {
    key: 'CN',
    code: 'construction',
    nameAr: 'المقاولات والمشاريع',
    nameEn: 'Construction',
    icon: '🏗️',
    descriptionAr: 'مقاولات عامة، تشطيب، سباكة، كهرباء، طرق',
    descriptionEn: 'General contracting, finishing, plumbing, electrical, roads',
    variableModules: {
      pos: false,
      stock: true,
      manufacturing: false,
      projects: true,
      services: true,
    },
  },
  SV: {
    key: 'SV',
    code: 'services',
    nameAr: 'الخدمات المهنية',
    nameEn: 'Professional Services',
    icon: '💼',
    descriptionAr: 'محاسبة، محاماة، استشارات، تدريب، تسويق',
    descriptionEn: 'Accounting, law, consulting, training, marketing',
    variableModules: {
      pos: false,
      stock: false,
      manufacturing: false,
      projects: true,
      services: true,
    },
  },
  PH: {
    key: 'PH',
    code: 'pharmacy',
    nameAr: 'الصيدليات والمستلزمات الطبية',
    nameEn: 'Pharmacy & Medical',
    icon: '💊',
    descriptionAr: 'صيدليات، مستلزمات طبية، مختبرات، عيادات صغيرة',
    descriptionEn: 'Pharmacies, medical supplies, labs, small clinics',
    variableModules: {
      pos: true,
      stock: true,
      manufacturing: false,
      projects: false,
      services: false,
    },
  },
  WK: {
    key: 'WK',
    code: 'workshop',
    nameAr: 'الورش والصيانة',
    nameEn: 'Workshops & Repair',
    icon: '🔧',
    descriptionAr: 'ميكانيك، كهرباء سيارات، صيانة أجهزة، نجارة',
    descriptionEn: 'Auto mechanics, electrical repair, device repair, carpentry',
    variableModules: {
      pos: true,
      stock: true,
      manufacturing: false,
      projects: false,
      services: true,
    },
  },
  EC: {
    key: 'EC',
    code: 'ecommerce',
    nameAr: 'التجارة الإلكترونية',
    nameEn: 'E-Commerce',
    icon: '🛒',
    descriptionAr: 'متاجر أونلاين، بيع عبر منصات التواصل، ماركت بليس',
    descriptionEn: 'Online stores, social media selling, marketplaces',
    variableModules: {
      pos: false,
      stock: true,
      manufacturing: false,
      projects: false,
      services: false,
    },
  },
  LG: {
    key: 'LG',
    code: 'logistics',
    nameAr: 'النقل والخدمات اللوجستية',
    nameEn: 'Logistics & Transport',
    icon: '🚛',
    descriptionAr: 'شحن، توصيل، مستودعات، نقل بضائع',
    descriptionEn: 'Freight, delivery, warehousing, cargo transport',
    variableModules: {
      pos: false,
      stock: true,
      manufacturing: false,
      projects: false,
      services: true,
    },
  },
  AG: {
    key: 'AG',
    code: 'agriculture',
    nameAr: 'الزراعة والتجارة الزراعية',
    nameEn: 'Agriculture',
    icon: '🌾',
    descriptionAr: 'مزارع، تجار محاصيل، أعلاف، دواجن',
    descriptionEn: 'Farms, crop traders, feed, poultry',
    variableModules: {
      pos: false,
      stock: true,
      manufacturing: false,
      projects: false,
      services: false,
    },
  },
  GN: {
    key: 'GN',
    code: 'general',
    nameAr: 'نشاط عام',
    nameEn: 'General / Multi-Activity',
    icon: '🌐',
    descriptionAr: 'شركة متنوعة النشاط — جميع الوحدات مفعّلة',
    descriptionEn: 'Multi-activity company — all modules enabled',
    variableModules: {
      pos: true,
      stock: true,
      manufacturing: true,
      projects: true,
      services: true,
    },
  },
}

/**
 * الحصول على قائمة الوحدات المفعّلة لنوع نشاط معين
 * @param {string} industryKey - كود النشاط (RT, FB, MF, CN, SV, WS, GN)
 * @returns {string[]} - قائمة مفاتيح الوحدات المفعّلة
 */
export function getEnabledModulesForIndustry(industryKey) {
  const industry = INDUSTRY_TYPES[industryKey]
  if (!industry) {
    // fallback to general
    return [...ALWAYS_ENABLED_MODULES, ...VARIABLE_MODULES]
  }

  const enabledVariable = Object.entries(industry.variableModules)
    .filter(([, enabled]) => enabled)
    .map(([key]) => key)

  return [...ALWAYS_ENABLED_MODULES, ...enabledVariable]
}

/**
 * التحقق هل الوحدة مفعّلة لنوع نشاط معين
 * @param {string} industryKey - كود النشاط
 * @param {string} moduleKey - مفتاح الوحدة
 * @returns {boolean}
 */
export function isModuleEnabledForIndustry(industryKey, moduleKey) {
  // Always-on modules
  if (ALWAYS_ENABLED_MODULES.includes(moduleKey)) return true

  const industry = INDUSTRY_TYPES[industryKey]
  if (!industry) return true // fallback: enable all

  return industry.variableModules[moduleKey] === true
}

/**
 * الحصول على قائمة أنواع الأنشطة كمصفوفة
 * @returns {Array}
 */
export function getIndustryTypesList() {
  return Object.values(INDUSTRY_TYPES)
}

// ===== Populate KEY_TO_CODE and CODE_TO_KEY maps =====
Object.values(INDUSTRY_TYPES).forEach(ind => {
  KEY_TO_CODE[ind.key] = ind.code
  CODE_TO_KEY[ind.code] = ind.key
})

/**
 * Convert short key (RT) or code name (retail) → code name
 * @param {string} input - RT or retail
 * @returns {string} - retail
 */
export function resolveIndustryCode(input) {
  if (!input) return 'general'
  if (KEY_TO_CODE[input]) return KEY_TO_CODE[input]
  if (CODE_TO_KEY[input]) return input // already a code
  return 'general'
}

/**
 * Convert code name (retail) or short key (RT) → short key
 * @param {string} input - retail or RT
 * @returns {string} - RT
 */
export function resolveIndustryKey(input) {
  if (!input) return 'GN'
  if (INDUSTRY_TYPES[input]) return input // already a key
  if (CODE_TO_KEY[input]) return CODE_TO_KEY[input]
  return 'GN'
}

// ===== خصائص الصفحات حسب النشاط =====
// كل مفتاح = ميزة في واجهة المستخدم
// القيمة = مصفوفة أكواد الأنشطة التي تُظهر هذه الميزة
// 'all' = جميع الأنشطة / null أو مفتاح غير موجود = يُظهر للكل
export const INDUSTRY_FEATURES = {
  // ------- بيع التجزئة (POS) -------
  'pos.table_management':   ['FB', 'GN'],                                     // إدارة الطاولات: مطاعم فقط
  'pos.kitchen_display':    ['FB', 'GN'],                                     // شاشة المطبخ: مطاعم فقط
  'pos.customer_display':   ['RT', 'FB', 'PH', 'WK', 'GN'],                  // شاشة العميل: أنشطة بها POS
  'pos.loyalty':            ['RT', 'FB', 'PH', 'GN'],                        // برامج الولاء: تجزئة وصيدليات
  'pos.promotions':         ['RT', 'FB', 'PH', 'WK', 'GN'],                  // العروض والخصومات

  // ------- المبيعات -------
  'sales.contracts':        ['SV', 'CN', 'MF', 'LG', 'WS', 'AG', 'WK', 'GN'], // عقود البيع: أنشطة B2B والمشاريع
  'sales.commissions':      'all',                                            // العمولات: جميع الأنشطة

  // ------- المشتريات -------
  'buying.rfq':             ['WS', 'MF', 'CN', 'LG', 'AG', 'GN'],           // طلب عروض الأسعار: مشتريات ضخمة
  'buying.agreements':      ['WS', 'MF', 'CN', 'LG', 'AG', 'WK', 'GN'],    // اتفاقيات الموردين
  'buying.supplier_ratings':['WS', 'MF', 'CN', 'GN'],                       // تقييم الموردين

  // ------- CRM -------
  'crm.campaigns':          ['RT', 'FB', 'EC', 'SV', 'WK', 'WS', 'GN'],    // الحملات التسويقية
  'crm.knowledge_base':     ['SV', 'WK', 'CN', 'LG', 'MF', 'GN'],         // قاعدة المعرفة: شركات الخدمات

  // ------- الموارد البشرية -------
  'hr.custody':             ['MF', 'CN', 'WK', 'LG', 'GN'],                // عهد الموظفين: صناعة وورش
  'hr.overtime':            ['MF', 'CN', 'WK', 'LG', 'FB', 'RT', 'GN'],   // الإضافي: أنشطة بها وردية
  'hr.gosi':                'all',                                           // التأمينات: جميع الأنشطة
  'hr.training':            'all',                                           // التدريب: جميع الأنشطة
}

/**
 * تحقق إذا كانت الميزة تظهر لنشاط معين
 * @param {string} featureKey - مفتاح الميزة مثل 'pos.table_management'
 * @param {string} industryKey - رمز النشاط مثل 'RT', 'FB'
 * @returns {boolean}
 */
export function hasIndustryFeature(featureKey, industryKey) {
  const rule = INDUSTRY_FEATURES[featureKey]
  if (!rule) return true              // ميزة غير مُعرَّفة → تظهر دائماً
  if (rule === 'all') return true     // جميع الأنشطة
  if (!industryKey) return true       // لا يوجد نشاط محدد → تظهر
  return rule.includes(industryKey)
}

export default INDUSTRY_TYPES
