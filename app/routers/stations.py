import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database_layer.database import get_db
from app.database_layer.models import Station
from app.data_transfer_schemas.schemas import StationCreate, StationResponse
from app.routers.auth import admin_required  # JWT admin dependency
from app.logger import get_logger

router = APIRouter(prefix="/stations", tags=["stations"])


# We inject the logger via Depends so FastAPI manages its lifecycle and
# it can be easily swapped or mocked in tests, just like the DB session.
@router.get("/", response_model=List[StationResponse])
async def get_stations(
    db: AsyncSession = Depends(get_db),
    logger: logging.Logger = Depends(get_logger),
):
    logger.info("GET /stations")
    result = await db.execute(select(Station))
    stations = result.scalars().all()
    logger.info(f"Response 200 - {len(stations)} stations returned")
    return stations


@router.post("/", response_model=StationResponse)
async def create_station(
    station: StationCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(admin_required),  # admin only — return value unused, dependency guards access
    logger: logging.Logger = Depends(get_logger),
):
    logger.info(f"POST /stations - input: name={station.name}, location={station.location}")
    new_station = Station(
        name=station.name,
        location=station.location
    )

    db.add(new_station)
    try:
        await db.commit()
        await db.refresh(new_station)
    except Exception as e:
        logger.error(f"Failed to create station '{station.name}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    logger.info(f"Response 201 - Station created with id={new_station.id}")
    return new_station


@router.delete("/{station_id}")
async def delete_station(
    station_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(admin_required),  # admin only — return value unused, dependency guards access
    logger: logging.Logger = Depends(get_logger),
):
    logger.info(f"DELETE /stations/{station_id}")
    result = await db.execute(select(Station).where(Station.id == station_id))
    station = result.scalar_one_or_none()

    if station is None:
        logger.warning(f"Response 404 - Station {station_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Station not found")

    try:
        await db.delete(station)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to delete station {station_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    logger.info(f"Response 200 - Station {station_id} deleted")
    return {"message": "Station deleted"}