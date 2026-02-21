
import json
import os

file_path = '/home/omar/Desktop/aman/frontend/src/locales/ar.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Update Manufacturing
mfg = data.get('manufacturing', {})
mfg['routes'] = "مسارات التصنيع"
mfg['active_boms'] = "قوائم المواد النشطة"
mfg['cost_per_hour'] = "التكلفة بالساعة"
mfg['daily_capacity'] = "السعة اليومية"
data['manufacturing'] = mfg

# Update Common
common = data.get('common', {})
common['id'] = "المعرف"
common['due_date'] = "تاريخ الاستحقاق"
data['common'] = common

# Add Products for compatibility
if 'products' not in data:
    data['products'] = {}
data['products']['product'] = "المنتج"

# Add top level
data['no_orders_found'] = "لم يتم العثور على أوامر تصنيع"

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Successfully updated ar.json with requested translations")
