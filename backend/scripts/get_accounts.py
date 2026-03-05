#!/usr/bin/env python3
"""Get account IDs from company ba2f6dc3"""
import requests, json

API = "http://64.225.49.118/api"
resp = requests.post(f"{API}/auth/login", data={"username":"vvvv","password":"As123321","company_code":"ba2f6dc3"})
token = resp.json()["access_token"]
H = {"Authorization": f"Bearer {token}"}

# Get all accounts
r = requests.get(f"{API}/accounting/accounts", headers=H)
accounts = r.json()

print(f"Total accounts: {len(accounts)}")
for a in sorted(accounts, key=lambda x: x.get('account_number','')):
    print(f"  id={a['id']:3d}  {a['account_number']:10s}  {a.get('account_code',''):12s}  {a['name']}")

# Get settings
print("\n=== Key Settings ===")
r2 = requests.get(f"{API}/settings", headers=H)
settings = r2.json()
for k in ['default_currency','company_country','vat_rate','fiscal_year_start','company_name','company_name_en']:
    print(f"  {k}: {settings.get(k, 'NOT SET')}")

# Get units
print("\n=== Units ===")
r3 = requests.get(f"{API}/inventory/units", headers=H)
print(json.dumps(r3.json(), ensure_ascii=False, indent=2)[:500])
