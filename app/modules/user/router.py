import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.limiter import limiter
from app.core.security import create_access_token
from app.dependencies import get_current_user, get_db

from .model import (
    LoginInput,
    RefreshInput,
    RefreshTokenOut,
    TokenOut,
    UserCreate,
    UserOut,
)
from .service import (
    authenticate_user,
    create_refresh_token,
    create_user,
    revoke_all_user_refresh_tokens,
    rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])

logger = logging.getLogger(__name__)

REFRESH_TOKEN_COOKIE = "refresh_token"
REFRESH_TOKEN_EXPIRE_DAYS = 30


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
        path="/auth",
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    body: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserOut:
    try:
        return await create_user(db, body)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error in /register")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.post("/login", response_model=RefreshTokenOut, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginInput,
    response: Response,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> RefreshTokenOut:
    try:
        user = await authenticate_user(db, body.email, body.password)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token({"sub": user.id})
        refresh_token = await create_refresh_token(db, user.id)
        _set_refresh_cookie(response, refresh_token)
        return RefreshTokenOut(
            access_token=access_token,
            refresh_token=refresh_token,  # nosec B106
            token_type="bearer",
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error in /login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.post("/refresh", response_model=TokenOut)
async def refresh(
    response: Response,
    db: AsyncIOMotorDatabase = Depends(get_db),
    cookie_token: str | None = Cookie(None, alias=REFRESH_TOKEN_COOKIE),
    body: RefreshInput | None = None,
) -> TokenOut:
    token = cookie_token or (body and body.refresh_token)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await rotate_refresh_token(db, token)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_refresh_token, user_id = result
    new_access_token = create_access_token({"sub": user_id})
    _set_refresh_cookie(response, new_refresh_token)
    return TokenOut(access_token=new_access_token, token_type="bearer")  # nosec B106


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    current_user: Annotated[UserOut, Depends(get_current_user)],
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> None:
    await revoke_all_user_refresh_tokens(db, current_user.id)
    response.delete_cookie(REFRESH_TOKEN_COOKIE, path="/auth")


@router.get("/me", response_model=UserOut)
async def read_me(
    current_user: Annotated[UserOut, Depends(get_current_user)],
) -> UserOut:
    return current_user
