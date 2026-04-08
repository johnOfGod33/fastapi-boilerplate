from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status

from .core.database import shutdown_mongodb, start_up_mongodb


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
