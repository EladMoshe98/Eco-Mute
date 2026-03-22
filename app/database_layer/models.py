from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, ForeignKey, CheckConstraint



class Base(DeclarativeBase):
    pass


class Bike(Base):
    __tablename__ = "bikes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model: Mapped[str] = mapped_column(String(100))
    battery: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30))
    station_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stations.id"), nullable=True, default=None)

    rentals = relationship("Rental", back_populates="bike")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('admin', 'user')", name="ck_users_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)  # <-- ADD THIS
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    rentals = relationship("Rental", back_populates="user")

    #lab6 - security
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)


class Rental(Base):
    __tablename__ = "rentals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    bike_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bikes.id", ondelete="SET NULL"), nullable=True)

    user = relationship("User", back_populates="rentals")
    bike = relationship("Bike", back_populates="rentals")

class Station(Base):
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str] = mapped_column(String(150), nullable=False)