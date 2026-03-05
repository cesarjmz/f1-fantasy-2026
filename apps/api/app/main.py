from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import router as v1_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.models import gameplay, reference, ruleset, simulation  # noqa: F401


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Schema creation is migration-driven; startup keeps side effects minimal.
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
register_exception_handlers(app)
app.include_router(v1_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
