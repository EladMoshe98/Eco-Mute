import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.exc import IntegrityError

from app.data_transfer_schemas.schemas import UserCreate, UserResponse
from app.database_layer.database import get_db
from app.database_layer.models import User

from app.security import get_password_hash
from app.logger import get_logger


router = APIRouter(prefix="/users", tags=["users"])


def user_to_response(u: User) -> UserResponse:
    return UserResponse(id=u.id, username=u.username, is_active=u.is_active)


@router.get("/", response_model=list[UserResponse])
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
):
    logger.info("GET /users")
    result = await db.execute(select(User))
    users = result.scalars().all()
    response = [user_to_response(u) for u in users]
    logger.info(f"Response 200 - {len(response)} users returned")
    return response


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
):
    logger.info(f"GET /users/{user_id}")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        logger.warning(f"Response 404 - User {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"Response 200 - User {user_id} found")
    return user_to_response(user)


@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
):
    logger.info(f"POST /users - input: username={user.username}, email={user.email}")

    # hash the password first (wrap to convert errors into 422)
    try:
        hashed_pw = get_password_hash(user.password)
    except ValueError as e:
        logger.error(f"Password hashing failed for user {user.username}: {e}")
        raise HTTPException(status_code=422, detail=str(e))

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pw,
        role=user.role,
        is_active=True
    )

    db.add(new_user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        logger.warning(f"Response 409 - Username or email already exists: {user.username} / {user.email}")
        raise HTTPException(status_code=409, detail="Username or email already exists")
    except Exception as e:
        logger.error(f"Failed to create user {user.username}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    await db.refresh(new_user)
    logger.info(f"Response 201 - User created with id={new_user.id}")
    return user_to_response(new_user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
):
    logger.info(f"DELETE /users/{user_id}")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning(f"Response 404 - User {user_id} not found for deletion")
        raise HTTPException(status_code=404, detail="User not found")

    try:
        await db.delete(user)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    logger.info(f"Response 200 - User {user_id} deleted")
    return {"message": "User deleted"}
