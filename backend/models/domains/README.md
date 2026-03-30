# Domain Facades for Models

This folder provides business-domain entry points for models while preserving full
compatibility with existing phase-based model files.

Use these modules for new code navigation and imports in new services.

## Why this exists

- Faster onboarding: models are grouped by business capability.
- Lower merge pressure: fewer edits to one giant list during parallel work.
- Better maintainability: code ownership and tests map to business domains.

## Domain Modules

- core.py
- sales.py
- procurement.py
- inventory.py
- manufacturing.py
- finance.py
- hr.py
- projects_crm.py
- operations.py
- security_reporting.py

Each domain module imports canonical model classes from `backend.models` and exposes
an explicit `__all__` list.
