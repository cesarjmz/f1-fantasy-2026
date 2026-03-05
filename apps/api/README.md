# API Service

## Local Setup

1. Create or activate your Python environment.
2. Install dependencies:

```powershell
pip install -e .
```

3. Set `DATABASE_URL` if you are not using the default sqlite path.

## Migration-First Database Boot

The API does not create tables at startup. Apply migrations before running the server.

From `apps/api`:

```powershell
alembic upgrade head
```

If you need to create a new migration after model changes:

```powershell
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Run API

```powershell
uvicorn app.main:app --reload
```

## Run Tests

```powershell
pytest -q
```
