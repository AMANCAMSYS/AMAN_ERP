# Backend Model Organization

This package currently contains two structures:

1. Historical phase files (`phase*.py`) used during the incremental ORM rollout.
2. Domain-first facades under `backend/models/domains/` for easier long-term maintenance.

The phase files are still valid and are kept for rollout traceability. For new development,
use the domain-first organization.

## Developer Note (New Contributors)

- It is easier for any new developer to find a model by business domain rather than by phase number.
- Merge conflicts are reduced because developers do not keep editing one large centralized import block for every change.
- Development, maintenance, and testing become closer to business logic boundaries.

## Rules Going Forward

- Do not create new `phaseXX_*.py` files for new features.
- Add new models in the relevant business domain and expose them through the domain facade.
- Keep `backend/models/__init__.py` as the compatibility export surface for existing imports.
- Keep table-to-model mapping one-to-one and explicit.

## Transition Strategy

- Phase files remain as a stable compatibility layer.
- Domain facades are the preferred entry point for model discovery and new code.
- Physical consolidation of phase files can be done later in small, safe batches.

## Migration Status

- Wave 1 complete: physical model definitions from phase 32 and phase 33 moved into
	`backend/models/domain_models/` grouped by business domains.
- `phase32_*` and `phase33_*` are now compatibility wrappers that re-export from domain modules.
