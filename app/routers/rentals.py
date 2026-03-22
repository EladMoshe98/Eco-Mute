import logging

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_layer.database import get_db
from app.database_layer.models import Rental, Bike, User
from app.logger import get_logger

router = APIRouter(prefix="/rentals", tags=["rentals"])


def rental_to_dict(r: Rental) -> Dict[str, Any]:
    """Minimal serializer to return JSON-friendly data."""
    return {"id": r.id, "user_id": r.user_id, "bike_id": r.bike_id}


@router.get("/", response_model=List[Dict[str, Any]])
async def list_rentals(
    db: AsyncSession = Depends(get_db),
    # We inject the logger via Depends so FastAPI manages its lifecycle and
    # it can be easily swapped or mocked in tests, just like the DB session.
    logger: logging.Logger = Depends(get_logger),
):
    """
    Return all rentals.
    """
    logger.info("GET /rentals")
    result = await db.execute(select(Rental))
    rentals = result.scalars().all()
    response = [rental_to_dict(r) for r in rentals]
    logger.info(f"Response 200 - {len(response)} rentals returned")
    return response


@router.get("/{rental_id}", response_model=Dict[str, Any])
async def get_rental(
    rental_id: int,
    db: AsyncSession = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
):
    """
    Return one rental by id.
    """
    logger.info(f"GET /rentals/{rental_id}")
    result = await db.execute(select(Rental).where(Rental.id == rental_id))
    rental = result.scalar_one_or_none()
    if rental is None:
        logger.warning(f"Response 404 - Rental {rental_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental not found")
    logger.info(f"Response 200 - Rental {rental_id} found")
    return rental_to_dict(rental)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
async def create_rental(
    user_id: int,
    bike_id: int,
    db: AsyncSession = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
):
    """
    Create a rental:
    - Validate bike exists and battery >= 20
    - Validate user exists
    - Mark bike as 'rented' and create a Rental row atomically
    """
    logger.info(f"POST /rentals - user_id={user_id}, bike_id={bike_id}")

    # load bike
    bike_res = await db.execute(select(Bike).where(Bike.id == bike_id))
    bike = bike_res.scalar_one_or_none()
    if bike is None:
        logger.warning(f"Response 404 - Bike {bike_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bike not found")

    # business rule: battery must be >= 20 to start rental
    if getattr(bike, "battery", 0) < 20:
        logger.warning(f"Response 400 - Bike {bike_id} battery too low ({bike.battery})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bike battery too low for rental")

    # optional: reject if already rented
    if getattr(bike, "status", "").lower() == "rented":
        logger.warning(f"Response 400 - Bike {bike_id} already rented")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bike already rented")

    # load user
    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()
    if user is None:
        logger.warning(f"Response 404 - User {user_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # create rental and update bike status
    new_rental = Rental(user_id=user_id, bike_id=bike_id)
    db.add(new_rental)
    # modify bike in same session so both commit together
    bike.status = "rented"

    try:
        await db.commit()           # commit both new_rental and bike.status change
        await db.refresh(new_rental)  # get id and any defaults populated
    except Exception as e:
        logger.error(f"Failed to create rental for user={user_id}, bike={bike_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    logger.info(f"Response 201 - Rental created with id={new_rental.id}")
    return rental_to_dict(new_rental)


@router.post("/{rental_id}/end", response_model=Dict[str, Any])
async def end_rental(
    rental_id: int,
    db: AsyncSession = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
):
    """
    End a rental (mark bike available again).
    This does not delete the rental row — it keeps history.
    """
    logger.info(f"POST /rentals/{rental_id}/end")
    res = await db.execute(select(Rental).where(Rental.id == rental_id))
    rental = res.scalar_one_or_none()
    if rental is None:
        logger.warning(f"Response 404 - Rental {rental_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental not found")

    # load bike and mark available
    bike_res = await db.execute(select(Bike).where(Bike.id == rental.bike_id))
    bike = bike_res.scalar_one_or_none()
    if bike is None:
        # this is unexpected but handle gracefully
        logger.error(f"Response 500 - Associated bike {rental.bike_id} not found for rental {rental_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Associated bike not found")

    bike.status = "available"
    try:
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to end rental {rental_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    logger.info(f"Response 200 - Rental {rental_id} ended, bike {rental.bike_id} now available")
    return rental_to_dict(rental)

