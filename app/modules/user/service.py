import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    get_password_hash,
    verify_password,
)

from .model import UserCreate, UserInDB, UserOut

USERS_COLLECTION = "users"
REFRESH_TOKENS_COLLECTION = "refresh_tokens"


def _doc_to_user_out(doc: dict) -> UserOut:
    return UserOut(
        id=str(doc["_id"]),
        email=doc["email"],
        username=doc["username"],
        first_name=doc["first_name"],
        last_name=doc["last_name"],
        created_at=doc["created_at"],
    )


def _doc_to_user_in_db(doc: dict) -> UserInDB:
    return UserInDB.model_validate(doc)


async def create_user(db: AsyncIOMotorDatabase, user: UserCreate) -> UserOut:
    existing = await db[USERS_COLLECTION].find_one({"email": user.email})
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    existing_username = await db[USERS_COLLECTION].find_one({"username": user.username})
    if existing_username is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken.",
        )
    now = datetime.now(timezone.utc)
    doc = {
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "hashed_password": get_password_hash(user.password),
        "created_at": now,
        "updated_at": now,
        "is_active": True,
    }
    result = await db[USERS_COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_user_out(doc)


async def authenticate_user(
    db: AsyncIOMotorDatabase, email: str, password: str
) -> UserInDB | None:
    doc = await db[USERS_COLLECTION].find_one({"email": email})
    if doc is None:
        verify_password(password, DUMMY_PASSWORD_HASH)
        return None
    if not verify_password(password, doc["hashed_password"]):
        return None
    if not doc.get("is_active", False):
        return None
    return _doc_to_user_in_db(doc)


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> UserOut | None:
    try:
        oid = ObjectId(user_id)
    except InvalidId:
        return None
    doc = await db[USERS_COLLECTION].find_one({"_id": oid})
    if doc is None:
        return None
    return _doc_to_user_out(doc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def create_refresh_token(
    db: AsyncIOMotorDatabase,
    user_id: str,
    family_id: str | None = None,
) -> str:
    token = secrets.token_urlsafe(64)
    now = datetime.now(timezone.utc)
    doc = {
        "token_hash": _hash_token(token),
        "user_id": ObjectId(user_id),
        "family_id": family_id or str(uuid.uuid4()),
        "expires_at": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "revoked": False,
        "created_at": now,
    }
    await db[REFRESH_TOKENS_COLLECTION].insert_one(doc)
    return token


async def rotate_refresh_token(
    db: AsyncIOMotorDatabase,
    token: str,
) -> tuple[str, str] | None:
    token_hash = _hash_token(token)
    now = datetime.now(timezone.utc)

    doc = await db[REFRESH_TOKENS_COLLECTION].find_one({"token_hash": token_hash})
    if doc is None:
        return None

    if doc["revoked"]:
        # Token reuse detected — revoke entire family (possible theft)
        await db[REFRESH_TOKENS_COLLECTION].update_many(
            {"family_id": doc["family_id"]},
            {"$set": {"revoked": True}},
        )
        return None

    expires_at = doc["expires_at"].replace(tzinfo=timezone.utc)
    if expires_at < now:
        return None

    await db[REFRESH_TOKENS_COLLECTION].update_one(
        {"_id": doc["_id"]},
        {"$set": {"revoked": True}},
    )

    user_id = str(doc["user_id"])
    new_token = await create_refresh_token(db, user_id, family_id=doc["family_id"])
    return new_token, user_id


async def revoke_all_user_refresh_tokens(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> None:
    await db[REFRESH_TOKENS_COLLECTION].update_many(
        {"user_id": ObjectId(user_id), "revoked": False},
        {"$set": {"revoked": True}},
    )
