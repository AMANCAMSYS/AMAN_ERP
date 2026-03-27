
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
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/16eb4eba-cd19-49d2-9df1-c824f3c729b3/c243be32-d4a8-4c45-a5ec-2b42fb050876
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC002 post api auth 2fa verify success
- **Test Code:** [TC002_post_api_auth_2fa_verify_success.py](./TC002_post_api_auth_2fa_verify_success.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 43, in <module>
  File "<string>", line 33, in test_post_api_auth_2fa_verify_success
AssertionError: 2FA verify failed: {"detail":"Not Found"}

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/16eb4eba-cd19-49d2-9df1-c824f3c729b3/2fb3994f-1114-4cea-9799-9049d0d76db6
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC003 get api companies authorized access
- **Test Code:** [TC003_get_api_companies_authorized_access.py](./TC003_get_api_companies_authorized_access.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 81, in <module>
  File "<string>", line 38, in test_get_api_companies_authorized_access
AssertionError: Companies retrieval failed: {"detail":"Not Found"}

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/16eb4eba-cd19-49d2-9df1-c824f3c729b3/86169c4b-c04e-4230-bba6-817fb7ba75a6
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC004 post api roles create role with permissions
- **Test Code:** [TC004_post_api_roles_create_role_with_permissions.py](./TC004_post_api_roles_create_role_with_permissions.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/16eb4eba-cd19-49d2-9df1-c824f3c729b3/e035a1ae-9d3a-453d-af97-6e40d8b4d7b0
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC005 get api finance accounting entries list
- **Test Code:** [TC005_get_api_finance_accounting_entries_list.py](./TC005_get_api_finance_accounting_entries_list.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 89, in <module>
  File "<string>", line 38, in test_get_api_finance_accounting_entries_list
AssertionError: Expected 200 OK but got 404: {"detail":"Not Found"}

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/16eb4eba-cd19-49d2-9df1-c824f3c729b3/baeb84ef-6ac8-4c31-8891-ee2a112a8bb2
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC006 post api finance treasury transactions create
- **Test Code:** [TC006_post_api_finance_treasury_transactions_create.py](./TC006_post_api_finance_treasury_transactions_create.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 88, in <module>
  File "<string>", line 53, in test_post_api_finance_treasury_transactions_create
AssertionError: Expected 201 Created, got 404, response: {"detail":"Not Found"}

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/16eb4eba-cd19-49d2-9df1-c824f3c729b3/5d1648ef-b175-453a-a115-3c0f98d616b5
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC007 get api sales orders list
- **Test Code:** [TC007_get_api_sales_orders_list.py](./TC007_get_api_sales_orders_list.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/16eb4eba-cd19-49d2-9df1-c824f3c729b3/39304354-a04a-446c-b522-af3fd8eda24c
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC008 post api purchases orders create
- **Test Code:** [TC008_post_api_purchases_orders_create.py](./TC008_post_api_purchases_orders_create.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 81, in <module>
  File "<string>", line 60, in test_post_api_purchases_orders_create
AssertionError: Expected 201 Created, got 404: {"detail":"Not Found"}

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/16eb4eba-cd19-49d2-9df1-c824f3c729b3/841fbe10-7658-4b09-847c-06c7370d005e
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC009 get root serve frontend application shell
- **Test Code:** [TC009_get_root_serve_frontend_application_shell.py](./TC009_get_root_serve_frontend_application_shell.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 18, in <module>
  File "<string>", line 12, in test_get_root_serve_frontend_application_shell
AssertionError: Expected 'text/html' in Content-Type, got application/json

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/16eb4eba-cd19-49d2-9df1-c824f3c729b3/87c0d2e1-85de-40d6-bfa0-fb82b8af7076
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC010 get api docs access swagger documentation
- **Test Code:** [TC010_get_api_docs_access_swagger_documentation.py](./TC010_get_api_docs_access_swagger_documentation.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/16eb4eba-cd19-49d2-9df1-c824f3c729b3/b28a2216-05b0-460a-aee9-a89a6cbd59c5
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