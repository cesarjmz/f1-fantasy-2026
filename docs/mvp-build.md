# Plan: F1 Fantasy 2026 MVP Build

Build a production-shaped MVP first, then layer advanced modeling and live ingestion. Priorities are 2026 rules correctness, auditable scoring, and full six-page UI coverage.

## Local-Only Mode (No Docker/Infra)

1. This MVP plan is executed in local-only mode.
2. Do not add Docker, Compose, or infrastructure provisioning steps to this plan.
3. All testing and development should run directly in the local Python/Node environments.

## 1) Completed Work Ledger (As Of March 5, 2026)

1. Backend persistence baseline complete with FastAPI + SQLAlchemy + Alembic.
2. Migration-first startup enabled (no runtime `create_all`).
3. Core endpoints complete: calendar, ruleset, prices, simulations, predictions, optimize, briefing, lineup submit/current/by-round, lineup audit.
4. Lineup history family complete: `history`, `transfers`, `lifecycle`, `chips`.
5. History/chips filtering + pagination complete (`limit`, `offset`, `from_round`, `to_round`).
6. Typed API errors complete with global handlers and OpenAPI models (`400/404/422/500`).
7. Redis-capable cache layer complete with in-memory fallback.
8. Stable cache key strategy complete (ruleset hash + model version + data cut + request params).
9. Cache observability complete via `X-Cache` for simulations/optimize.
10. Cache invalidation endpoint complete: `POST /api/v1/cache/invalidate`.
11. Deterministic Monte Carlo baseline integrated for projections (`>=10,000` path supported).
12. Simulation run summary fields complete on predictions (`n_sims`, summary aggregates).
13. Lightweight simulation summary endpoint complete: `GET /api/v1/simulations/{run_id}/summary`.
14. Simulation predictions pagination complete with `limit` + `offset` + metadata.
15. Backend test suite passing at last verification: `31 passed`.

## 2) MVP Gaps Remaining

1. Optimizer depth is still baseline; needs richer risk/explanation payloads.
2. Frontend six-page implementation is not yet complete.
3. Worker + ingestion scaffolding is not yet implemented.
4. Hardening coverage (e2e, regression scenarios, docs/runbook completeness) remains.

## 3) Parallel Workstreams

### Stream A: Backend Simulation and Optimization

1. Add sorting controls to predictions (`sort_by`, `order`) with stable pagination.
2. Add optimizer rationale payload schema (why lineup ranked, chip recommendation factors).
3. Implement explicit optimizer modes behavior checks (Max EV, Upside, Downside, Value Growth, Chip-aware).
4. Add constraints diagnostics in optimize response (budget margin, chip eligibility, transfer assumptions).
5. Add simulation smoke performance assertion for `n_sims >= 10,000`.

### Stream B: API Contracts and Documentation

1. Sync `docs/api/mvp-api.md` with final query params and error examples for all simulation endpoints.
2. Add OpenAPI examples for success/error for high-traffic routes.
3. Add contract snapshots under `packages/api-contracts/rest` for simulation + lineup endpoints.
4. Add typed TS/Python DTO updates under `packages/types/ts` and `packages/types/py`.

### Stream C: Frontend MVP Pages

1. App shell + routing + typed client integration.
2. Implement `Dashboard` page with simulation summary cards.
3. Implement `Team Builder` with roster slots, budget bar, chips, optimize action.
4. Implement `Projections` page consuming predictions pagination.
5. Implement `Chip Planner` page using lineup history endpoints.
6. Implement `Race Week Briefing` page.
7. Implement `Score Audit` page.
8. Add mobile/responsive + loading/error states across all pages.

### Stream D: Workers and Ingestion Scaffolding

1. Add Celery app bootstrap under `workers/celery/app`.
2. Add scheduled tasks for seeded refresh and simulation reruns.
3. Add briefing regeneration task.
4. Add ingestion adapter interfaces/stubs for OpenF1/FastF1.
5. Add structured logging + tracing hooks.

### Stream E: QA and Release Hardening

1. Add golden fixtures for scoring/chips/transfers.
2. Add full API integration coverage for current endpoint surface.
3. Add frontend functional tests for six pages.
4. Add seeded end-to-end scenario test: lineup -> optimize -> simulate -> briefing -> audit.
5. Publish architecture/api/runbook/known-gaps docs.

## 4) Punctual Next Steps (Execution Order)

1. Backend: add predictions sorting (`sort_by`, `order`) with tests.
2. Backend: add optimizer explanation payload fields and tests.
3. API docs/contracts: publish updated simulation endpoint examples and contract snapshots.
4. Frontend: scaffold app shell + typed API client + simulation summary integration.
5. Frontend: deliver `Dashboard` first vertical slice.
6. Frontend: deliver `Projections` page wired to predictions pagination.
7. Frontend: deliver `Team Builder` with optimize + chips controls.
8. Workers: scaffold Celery and one scheduled rerun task.
9. QA: add Monte Carlo smoke/perf test gate and golden-round regression seed.
10. Release docs: update runbook with cache invalidation + simulation endpoint usage.

## 5) Dependency Gates

1. Gate G1: API contract freeze for simulation endpoints before full frontend page work.
2. Gate G2: Optimizer explanation payload finalization before Team Builder UX final pass.
3. Gate G3: Celery task scaffold before ingestion adapter expansion.
4. Gate G4: End-to-end seeded scenario green before release signoff.

## 6) Suggested Parallel Assignment (If Multiple Contributors)

1. Contributor 1: Stream A (backend sim/optimizer).
2. Contributor 2: Stream C (frontend pages).
3. Contributor 3: Stream D (workers/ingestion).
4. Contributor 4: Stream B + E (contracts/docs + QA hardening).

## 7) Key Files

- `apps/api/app/api/v1.py`
- `apps/api/app/services/repository.py`
- `apps/api/app/services/simulation.py`
- `apps/api/tests/test_api.py`
- `apps/web/src/pages/*`
- `apps/web/src/services/api.ts`
- `workers/celery/app/tasks/*`
- `services/ingestion/app/*`
- `packages/api-contracts/rest/*`
- `packages/types/py/*`
- `packages/types/ts/*`
- `docs/api/mvp-api.md`
- `docs/architecture/mvp-architecture.md`

## 8) Decisions Captured

1. MVP target remains 2-3 weeks.
2. Seeded/mock data first, then live ingestion.
3. Single-user local mode only for MVP (no auth).
4. All six core pages are in MVP scope.
5. Workstream-based parallel execution is the preferred delivery model.
