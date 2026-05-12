from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .config import settings


async def start_up_mongodb(app: FastAPI) -> None:
    try:
        print("Connecting to MongoDB...")
        app.client = AsyncIOMotorClient(settings.MONGODB_URI)
        app.db = app.client[settings.MONGODB_DB_NAME]
    except Exception as e:
        raise RuntimeError(f"Failed to connect to MongoDB: {e}") from e


async def shutdown_mongodb(app: FastAPI) -> None:
    app.client.close()


async def create_indexes(db: AsyncIOMotorDatabase) -> None:
    await db["users"].create_index("email", unique=True)
    await db["users"].create_index("username", unique=True)
    await db["refresh_tokens"].create_index("token_hash", unique=True)
    await db["refresh_tokens"].create_index("expires_at", expireAfterSeconds=0)
