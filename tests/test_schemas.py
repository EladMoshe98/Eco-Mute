import pytest
from pydantic import ValidationError

from app.data_transfer_schemas.schemas import UserSignup, RentalProcessing


def test_user_signup_password_must_be_alnum_and_8_chars():
    with pytest.raises(ValidationError):
        UserSignup(email="a@b.com", password="short")  # < 8

    with pytest.raises(ValidationError):
        UserSignup(email="a@b.com", password="not_alnum!!")  # not alphanumeric

    ok = UserSignup(email="a@b.com", password="Password1")
    assert ok.email == "a@b.com"


def test_rental_processing_rejects_low_battery():
    with pytest.raises(ValidationError):
        RentalProcessing(bike_battery=10, user_id=1)

    ok = RentalProcessing(bike_battery=20, user_id=1)
    assert ok.bike_battery == 20