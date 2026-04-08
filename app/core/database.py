from fastapi import FastAPI
from pymongo import AsyncMongoClient

from .env_config import settings


async def start_up_mongodb(app: FastAPI):
    try:
        uri = settings.MONGODB_URI
        client = AsyncMongoClient(uri)
        db = client.get_database(settings.MONGODB_DB)
        app.client = client
        app.db = db
    except Exception as e:
        raise RuntimeError(f"Failed to connect to MongoDB: {e}")


async def shutdown_mongodb(app: FastAPI):
    await app.client.close()
    print("MongoDB connection closed")
