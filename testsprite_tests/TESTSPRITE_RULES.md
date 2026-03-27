# TestSprite Rules For This Project

Use these rules in every future backend test generation run.

## Environment
- Base URL: `http://localhost:8000`
- Auth type: Bearer token
- Login endpoint: `POST /api/auth/login`
- Login form fields: `username`, `password`, `company_code`

## Route map (do not use old/incorrect paths)
- Companies list: `GET /api/companies/list`
- Roles create: `POST /api/roles`
- Accounting entries list: `GET /api/accounting/journal-entries`
- Treasury accounts: `GET /api/treasury/accounts`
- Treasury transfer create: `POST /api/treasury/transactions/transfer`
- Purchase orders: `POST /api/buying/orders`
- Suppliers list/create: `GET/POST /api/inventory/suppliers`
- Sales orders list: `GET /api/sales/orders`
- Docs: `GET /api/docs`

## File creation quality rules
- Always generate runnable Python files with valid imports.
- Prefer importing shared helpers from `testsprite_tests._helpers` and scenarios from `testsprite_tests._scenarios`.
- Avoid hardcoding expired JWT tokens.
- Avoid `/api/finance/*` paths unless such routes are explicitly confirmed in code.
- If a scenario precondition is missing (example: no treasury accounts), fail with a clear assertion or exit gracefully by design.
