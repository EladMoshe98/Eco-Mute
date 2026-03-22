from fastapi import FastAPI

from contextlib import asynccontextmanager
from app.database_layer.database import engine
from app.database_layer.models import Base
from app.routers import auth, bikes, users, rentals, admin_router, stations

from app.routers.prediction import router as prediction_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(bikes.router)
app.include_router(users.router)
app.include_router(rentals.router)
app.include_router(admin_router.router)

# new stations router - lab6
app.include_router(auth.router)
app.include_router(stations.router)

# new prediction router - lab7
app.include_router(prediction_router)
