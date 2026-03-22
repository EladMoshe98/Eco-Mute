

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, EmailStr, model_validator


BikeStatus = Literal["available", "rented", "maintenance"]


class BikeBase(BaseModel):
    model: str
    battery_level: float = Field(ge=0, le=100) #make sure always 0<level<100
    status: BikeStatus
    station_id: Optional[int] = None

    @field_validator("battery_level")
    @classmethod
    def check_battery(cls, value):
        if value < 0:
            raise ValueError("Battery cannot be negative")
        return value


class BikeCreate(BikeBase):
    pass


class BikeResponse(BikeBase):
    id: int


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Literal["admin", "user"] = "user"

    @field_validator("password")
    @classmethod
    def min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v



class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool


class UserSignup(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")

        if not value.isalnum():
            raise ValueError("Password must be alphanumeric.")

        return value

class RentalOutcome(BaseModel):
    bike_id: int
    user_id: int
    bike_battery: int

    @field_validator("bike_battery")
    @classmethod
    def validate_battery(cls, value: int) -> int:
        if value < 20:
            raise ValueError("Cannot create rental. Bike battery below 20%.")
        return value

class RentalProcessing(BaseModel):
    bike_battery: int
    user_id: int

    @model_validator(mode="after")
    def check_battery(self):
        if self.bike_battery < 20:
            raise ValueError("Bike battery too low for rental.")
        return self




class StationBase(BaseModel):
    name: str
    location: str


class StationCreate(StationBase):
    pass


class StationResponse(StationBase):
    id: int
    model_config = {"from_attributes": True}


#ML part

class TripInput(BaseModel):
    distance_km: float = Field(..., gt=0, description="Trip distance in kilometers")
    battery_level: float = Field(..., ge=0, le=100, description="Battery percentage")