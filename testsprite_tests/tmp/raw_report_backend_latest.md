
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
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 38, in <module>
  File "<string>", line 22, in test_post_api_auth_login_success
AssertionError: Expected status code 200 but got 401

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/320a6acc-7fe0-408d-9e5d-c4576d584da7/1d526f25-92ba-4e5a-a988-21656a74d2b5
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC002 post api auth 2fa verify success
- **Test Code:** [TC002_post_api_auth_2fa_verify_success.py](./TC002_post_api_auth_2fa_verify_success.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 30, in <module>
  File "<string>", line 23, in test_post_api_auth_2fa_verify_success
AssertionError: Expected 200 OK, got 404

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/320a6acc-7fe0-408d-9e5d-c4576d584da7/28fc7e73-e378-4e76-b49a-ee2d70c1c5dc
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC003 get api companies authorized access
- **Test Code:** [TC003_get_api_companies_authorized_access.py](./TC003_get_api_companies_authorized_access.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 51, in <module>
  File "<string>", line 17, in test_get_api_companies_authorized_access
AssertionError: Expected status code 200, got 404

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/320a6acc-7fe0-408d-9e5d-c4576d584da7/7df62384-4bcd-43d5-b84a-dd9b4b3568a8
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC004 post api roles create role with permissions
- **Test Code:** [TC004_post_api_roles_create_role_with_permissions.py](./TC004_post_api_roles_create_role_with_permissions.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 76, in <module>
  File "<string>", line 35, in test_post_api_roles_create_role_with_permissions
AssertionError: Expected 201 Created but got 422, response: {"detail":[{"type":"missing","loc":["body","role_name"],"msg":"Field required","input":{"name":"test_role_04eb99fc","permissions":["accounting.manage","reports.view","sales.create","purchases.manage","treasury.transfer","taxes.apply"]}}]}

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/320a6acc-7fe0-408d-9e5d-c4576d584da7/9155044e-4295-40ac-a42f-8e8f862e1513
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC005 get api finance accounting entries list
- **Test Code:** [TC005_get_api_finance_accounting_entries_list.py](./TC005_get_api_finance_accounting_entries_list.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 77, in <module>
  File "<string>", line 34, in test_get_finance_accounting_entries_list
AssertionError: Expected status 200, got 404

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/320a6acc-7fe0-408d-9e5d-c4576d584da7/e9f9ecf5-53d0-450c-ba5e-62241d144ea1
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC006 post api finance treasury transactions create
- **Test Code:** [TC006_post_api_finance_treasury_transactions_create.py](./TC006_post_api_finance_treasury_transactions_create.py)
- **Test Error:** Traceback (most recent call last):
  File "<string>", line 28, in test_post_api_finance_treasury_transactions_create
AssertionError: Expected 201 Created but got 404, response: {"detail":"Not Found"}

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 52, in <module>
  File "<string>", line 49, in test_post_api_finance_treasury_transactions_create
AssertionError: Test failure: Expected 201 Created but got 404, response: {"detail":"Not Found"}

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/320a6acc-7fe0-408d-9e5d-c4576d584da7/71e3580b-8a02-411e-aaf0-6a2ed47edf66
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC007 get api sales orders list
- **Test Code:** [TC007_get_api_sales_orders_list.py](./TC007_get_api_sales_orders_list.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/320a6acc-7fe0-408d-9e5d-c4576d584da7/307b9708-d15e-46c8-adae-3f22ad2e9629
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC008 post api purchases orders create
- **Test Code:** [TC008_post_api_purchases_orders_create.py](./TC008_post_api_purchases_orders_create.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 66, in <module>
  File "<string>", line 15, in test_post_api_purchases_orders_create
AssertionError: Failed to get companies, status 404

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/320a6acc-7fe0-408d-9e5d-c4576d584da7/3b933af9-17ce-45d9-9efe-276528709e14
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC009 get root serve frontend application shell
- **Test Code:** [TC009_get_root_serve_frontend_application_shell.py](./TC009_get_root_serve_frontend_application_shell.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 27, in <module>
  File "<string>", line 15, in test_TC009_get_root_serve_frontend_application_shell
AssertionError: Expected Content-Type to include 'text/html', got 'application/json'

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/320a6acc-7fe0-408d-9e5d-c4576d584da7/3b68d2a7-6765-46d0-92d9-aecc78f94cb6
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC010 get api docs access swagger documentation
- **Test Code:** [TC010_get_api_docs_access_swagger_documentation.py](./TC010_get_api_docs_access_swagger_documentation.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/320a6acc-7fe0-408d-9e5d-c4576d584da7/2e2f3671-2d37-422f-b579-886f8b98ce2f
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---


## 3️⃣ Coverage & Matching Metrics

- **20.00** of tests passed

| Requirement        | Total Tests | ✅ Passed | ❌ Failed  |
|--------------------|-------------|-----------|------------|
| ...                | ...         | ...       | ...        |
---


## 4️⃣ Key Gaps / Risks
{AI_GNERATED_KET_GAPS_AND_RISKS}
---