import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data_transfer_schemas.schemas import BikeCreate, BikeResponse, BikeStatus
from app.database_layer.database import get_db
from app.database_layer.models import Bike
from app.logger import get_logger

router = APIRouter(prefix="/bikes", tags=["bikes"])


def bike_to_response(bike: Bike) -> BikeResponse:
    return BikeResponse(
        id=bike.id,
        model=bike.model,
        battery_level=bike.battery,  # map DB -> schema
        status=bike.status,
        station_id=bike.station_id
    )


@router.get("/", response_model=List[BikeResponse])
async def get_all_bikes(
    status: Optional[BikeStatus] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
):
    logger.info(f"GET /bikes - status filter: {status}")
    result = await db.execute(select(Bike))
    bikes = result.scalars().all()

    if status is not None:
        bikes = [b for b in bikes if b.status == status]

    response = [bike_to_response(b) for b in bikes]
    logger.info(f"Response 200 - {len(response)} bikes returned")
    return response


@router.get("/{bike_id}", response_model=BikeResponse)
async def get_bike_by_id(
    bike_id: int,
    db: AsyncSession = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
):
    logger.info(f"GET /bikes/{bike_id}")
    result = await db.execute(select(Bike).where(Bike.id == bike_id))
    bike = result.scalar_one_or_none()

    if bike is None:
        logger.warning(f"Response 404 - Bike {bike_id} not found")
        raise HTTPException(status_code=404, detail="Bike not found")

    logger.info(f"Response 200 - Bike {bike_id} found")
    return bike_to_response(bike)


@router.post("/", response_model=BikeResponse)
async def create_bike(
    bike: BikeCreate,
    db: AsyncSession = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
):
    logger.info(f"POST /bikes - input: {bike}")
    new_bike = Bike(
        model=bike.model,
        battery=int(bike.battery_level),
        status=bike.status,
    )

    try:
        db.add(new_bike)
        await db.commit()
        await db.refresh(new_bike)
    except Exception as e:
        logger.error(f"Failed to create bike: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    response = bike_to_response(new_bike)
    logger.info(f"Response 201 - Bike created with id={new_bike.id}")
    return response


@router.put("/{bike_id}", response_model=BikeResponse)
async def update_bike(
    bike_id: int,
    bike: BikeCreate,
    db: AsyncSession = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
):
    logger.info(f"PUT /bikes/{bike_id} - input: {bike}")
    result = await db.execute(select(Bike).where(Bike.id == bike_id))
    existing = result.scalar_one_or_none()

    if existing is None:
        logger.warning(f"Response 404 - Bike {bike_id} not found for update")
        raise HTTPException(status_code=404, detail="Bike not found")

    existing.model = bike.model
    existing.battery = int(bike.battery_level)
    existing.status = bike.status

    try:
        await db.commit()
        await db.refresh(existing)
    except Exception as e:
        logger.error(f"Failed to update bike {bike_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    logger.info(f"Response 200 - Bike {bike_id} updated")
    return bike_to_response(existing)


@router.delete("/{bike_id}")
async def delete_bike(
    bike_id: int,
    db: AsyncSession = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
):
    logger.info(f"DELETE /bikes/{bike_id}")
    result = await db.execute(select(Bike).where(Bike.id == bike_id))
    bike = result.scalar_one_or_none()

    if bike is None:
        logger.warning(f"Response 404 - Bike {bike_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Bike not found")

    try:
        await db.delete(bike)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to delete bike {bike_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    logger.info(f"Response 200 - Bike {bike_id} deleted")
    return {"message": "Bike deleted"}