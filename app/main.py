from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status

from .core.database import shutdown_mongodb, start_up_mongodb
from .modules.user.router import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_up_mongodb(app)
    yield
    await shutdown_mongodb(app)


app = FastAPI(
    title="Your API title",
    description="Your API description",
    version="1.0.0",
    lifespan=lifespan,
)

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
