from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .core.database import create_indexes, shutdown_mongodb, start_up_mongodb
from .core.limiter import limiter
from .modules.user.router import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_up_mongodb(app)
    await create_indexes(app.db)
    yield
    await shutdown_mongodb(app)


app = FastAPI(
    title="Your API title",
    description="Your API description",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(user_router)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health(request: Request):
    """Health check endpoint."""
    try:
        mongo_health = await request.app.client["admin"].command("ping")

        if mongo_health["ok"] == 1:
            return {"status": "ok", "mongo_health": mongo_health}
        else:
            raise RuntimeError("MongoDB is not healthy")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {"message": "What are you doing here?"}
