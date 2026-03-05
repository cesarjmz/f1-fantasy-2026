# F1 Fantasy MVP API Notes

## Error Envelope

All API errors return:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

`details` is optional and typically populated for validation failures.

## Cache Observability

`POST /api/v1/simulations/run` and `POST /api/v1/optimize` include `X-Cache` headers:

- `MISS`: response was computed and cache was written.
- `HIT`: response reused from cache for equivalent request key.

Cache keys are built from:

- ruleset hash
- model version
- data cut label
- canonical request parameters

## Cache Invalidation Endpoint

`POST /api/v1/cache/invalidate`

Query params:

- `namespace=all|projections|optimizer` (default: `all`)

Response:

```json
{
  "namespace": "optimizer",
  "deleted": 3
}
```

The endpoint is intended for local/dev workflows and deterministic test control.

## Simulation Baseline

`POST /api/v1/simulations/run` now uses a deterministic Monte Carlo baseline per asset.

- Configurable via request `n_sims`
- Designed for Phase 3 baseline usage at `>=10,000` sims
- Persists run metadata and summary distribution (`mean`, `median`, `p10`, `p90`, `prob_negative`)

`GET /api/v1/simulations/{run_id}/predictions` additionally returns:

- `n_sims`: persisted simulation count for the run
- `summary.entity_count`: number of projected entities in the run
- `summary.top_mean`: entity with highest mean projection
- `summary.highest_upside`: entity with highest `p90`
- `summary.highest_negative_risk`: entity with highest `prob_negative`

Optional query params:

- `limit` (`1..200`): truncates the returned `predictions` list size for lightweight fetches.
- `offset` (`>=0`): selects the starting index within the run predictions list.

Note: `summary.*` is still computed across the full persisted run, not the truncated subset.

Pagination metadata returned under `meta`:

- `total`, `limit`, `offset`, `returned`
- `has_more`, `next_offset`

## Simulation Summary Endpoint

`GET /api/v1/simulations/{run_id}/summary`

Returns run metadata and aggregate summary only (no full `predictions` list), useful for lighter dashboard polling.

Response fields:

- `run_id`, `season`, `round`, `n_sims`, `model_version`
- `summary.entity_count`
- `summary.top_mean`
- `summary.highest_upside`
- `summary.highest_negative_risk`
