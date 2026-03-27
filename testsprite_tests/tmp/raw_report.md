
# TestSprite AI Testing Report(MCP)

---

## 1️⃣ Document Metadata
- **Project Name:** aman
- **Date:** 2026-03-27
- **Prepared by:** TestSprite AI Team

---

## 2️⃣ Requirement Validation Summary

#### Test TC001 post api auth login success
- **Test Code:** [TC001_post_api_auth_login_success.py](./TC001_post_api_auth_login_success.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/295092be-69ef-430a-bfac-22a0503256be/c331594e-b4ac-487a-8473-0d372cdef995
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC002 post api auth 2fa verify success
- **Test Code:** [TC002_post_api_auth_2fa_verify_success.py](./TC002_post_api_auth_2fa_verify_success.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 50, in <module>
  File "<string>", line 39, in test_post_api_auth_2fa_verify_success
AssertionError: 2FA verify failed with status 404

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/295092be-69ef-430a-bfac-22a0503256be/52214fa4-503a-4f73-8463-872af37ba6e5
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC003 get api companies authorized access
- **Test Code:** [TC003_get_api_companies_authorized_access.py](./TC003_get_api_companies_authorized_access.py)
- **Test Error:** Traceback (most recent call last):
  File "<string>", line 34, in test_get_api_companies_authorized_access
AssertionError: Companies API responded with status 404

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 67, in <module>
  File "<string>", line 65, in test_get_api_companies_authorized_access
AssertionError: Companies request failed or invalid response: Companies API responded with status 404

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/295092be-69ef-430a-bfac-22a0503256be/192894a4-f3c0-4044-9d2b-f6354b537e17
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC004 post api roles create role with permissions
- **Test Code:** [TC004_post_api_roles_create_role_with_permissions.py](./TC004_post_api_roles_create_role_with_permissions.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/295092be-69ef-430a-bfac-22a0503256be/b20ec5ef-2763-4fc9-b1a5-162d808c3685
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC005 get api finance accounting entries list
- **Test Code:** [TC005_get_api_finance_accounting_entries_list.py](./TC005_get_api_finance_accounting_entries_list.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 82, in <module>
  File "<string>", line 43, in test_get_api_accounting_journal_entries_list
AssertionError: Expected 200 but got 404

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/295092be-69ef-430a-bfac-22a0503256be/88c224f0-0ac3-4e26-85c7-a6a5c4a61c35
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC006 post api finance treasury transactions create
- **Test Code:** [TC006_post_api_finance_treasury_transactions_create.py](./TC006_post_api_finance_treasury_transactions_create.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 90, in <module>
  File "<string>", line 49, in test_post_api_finance_treasury_transactions_create
AssertionError: Expected 201 Created, got 404

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/295092be-69ef-430a-bfac-22a0503256be/93ed849e-1d01-4dde-8751-207bdaabe09c
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC007 get api sales orders list
- **Test Code:** [TC007_get_api_sales_orders_list.py](./TC007_get_api_sales_orders_list.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/295092be-69ef-430a-bfac-22a0503256be/7cc01126-1284-4c51-a72c-75563c57ca9f
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC008 post api purchases orders create
- **Test Code:** [TC008_post_api_purchases_orders_create.py](./TC008_post_api_purchases_orders_create.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 62, in <module>
  File "<string>", line 51, in test_create_purchase_order
AssertionError: Expected 201 Created, got 404

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/295092be-69ef-430a-bfac-22a0503256be/8ab1b83f-e3cb-4318-a9d5-a1f9daed87f5
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC009 get root serve frontend application shell
- **Test Code:** [TC009_get_root_serve_frontend_application_shell.py](./TC009_get_root_serve_frontend_application_shell.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 22, in <module>
  File "<string>", line 13, in test_get_root_serve_frontend_application_shell
AssertionError

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/295092be-69ef-430a-bfac-22a0503256be/4203ae74-4e2d-48dd-8a92-3d66d13f95e2
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC010 get api docs access swagger documentation
- **Test Code:** [TC010_get_api_docs_access_swagger_documentation.py](./TC010_get_api_docs_access_swagger_documentation.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/295092be-69ef-430a-bfac-22a0503256be/6541722e-f568-4eb9-9aa3-b02776fe86fc
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---


## 3️⃣ Coverage & Matching Metrics

- **40.00** of tests passed

| Requirement        | Total Tests | ✅ Passed | ❌ Failed  |
|--------------------|-------------|-----------|------------|
| ...                | ...         | ...       | ...        |
---


## 4️⃣ Key Gaps / Risks
{AI_GNERATED_KET_GAPS_AND_RISKS}
---