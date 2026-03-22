"""
Edge-case and improper-input tests.
Covers: boundary values, missing/wrong-typed fields, business-rule violations,
invalid JWT, rental lifecycle, and role enforcement.
"""
import pytest


# ══════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════

async def _make_user(client, username="u1", password="password1", role="user"):
    resp = await client.post("/users/", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": password,
        "role": role,
    })
    return resp.json()


async def _login(client, username, password):
    resp = await client.post("/auth/token", data={"username": username, "password": password})
    return resp.json().get("access_token", "")


async def _make_admin_token(client):
    await _make_user(client, username="admin_u", password="adminpass1", role="admin")
    return await _login(client, "admin_u", "adminpass1")


async def _make_bike(client, battery=80, status="available"):
    resp = await client.post("/bikes/", json={"model": "TestBike", "battery_level": battery, "status": status})
    return resp.json()


# ══════════════════════════════════════════════════════════
#  USERS – field validation edge cases
# ══════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_create_user_invalid_role_422(client):
    """Role must be 'admin' or 'user'; anything else → 422."""
    resp = await client.post("/users/", json={
        "username": "hacker", "email": "h@test.com",
        "password": "password1", "role": "superuser",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_user_missing_email_422(client):
    """Omitting email entirely → 422."""
    resp = await client.post("/users/", json={"username": "x", "password": "password1", "role": "user"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_user_missing_password_422(client):
    """Omitting password entirely → 422."""
    resp = await client.post("/users/", json={"username": "x", "email": "x@test.com", "role": "user"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_user_missing_username_422(client):
    """Omitting username → 422."""
    resp = await client.post("/users/", json={"email": "x@test.com", "password": "password1", "role": "user"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_user_password_exactly_8_chars_ok(client):
    """Password of exactly 8 chars should be accepted (boundary)."""
    resp = await client.post("/users/", json={
        "username": "eightpw", "email": "eight@test.com",
        "password": "12345678", "role": "user",
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_create_user_password_7_chars_rejected(client):
    """Password of 7 chars is one below the minimum → 422."""
    resp = await client.post("/users/", json={
        "username": "sevenpw", "email": "seven@test.com",
        "password": "1234567", "role": "user",
    })
    assert resp.status_code == 422


# ══════════════════════════════════════════════════════════
#  BIKES – boundary values & missing fields
# ══════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_create_bike_battery_0_ok(client):
    """Battery level exactly 0 should be accepted (lower boundary)."""
    resp = await client.post("/bikes/", json={"model": "Empty", "battery_level": 0, "status": "available"})
    assert resp.status_code == 200
    assert resp.json()["battery_level"] == 0


@pytest.mark.asyncio
async def test_create_bike_battery_100_ok(client):
    """Battery level exactly 100 should be accepted (upper boundary)."""
    resp = await client.post("/bikes/", json={"model": "Full", "battery_level": 100, "status": "available"})
    assert resp.status_code == 200
    assert resp.json()["battery_level"] == 100


@pytest.mark.asyncio
async def test_create_bike_battery_101_rejected(client):
    """Battery level 101 is one above maximum → 422."""
    resp = await client.post("/bikes/", json={"model": "Over", "battery_level": 101, "status": "available"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_bike_missing_model_422(client):
    """Omitting model field → 422."""
    resp = await client.post("/bikes/", json={"battery_level": 80, "status": "available"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_bike_missing_status_422(client):
    """Omitting status field → 422."""
    resp = await client.post("/bikes/", json={"model": "X", "battery_level": 80})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_bike_string_battery_422(client):
    """Passing a non-numeric string for battery → 422."""
    resp = await client.post("/bikes/", json={"model": "X", "battery_level": "full", "status": "available"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_bike_by_string_id_422(client):
    """Passing a non-integer path parameter → 422."""
    resp = await client.get("/bikes/abc")
    assert resp.status_code == 422


# ══════════════════════════════════════════════════════════
#  STATIONS – missing / empty fields
# ══════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_create_station_missing_name_422(client):
    """Omitting name → 422."""
    token = await _make_admin_token(client)
    resp = await client.post(
        "/stations/",
        json={"location": "Somewhere"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_station_missing_location_422(client):
    """Omitting location → 422."""
    token = await _make_admin_token(client)
    resp = await client.post(
        "/stations/",
        json={"name": "Station A"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


# ══════════════════════════════════════════════════════════
#  AUTH – token tampering
# ══════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_garbage_token_401(client):
    """A completely garbage bearer token → 401."""
    resp = await client.post(
        "/stations/",
        json={"name": "S", "location": "L"},
        headers={"Authorization": "Bearer this.is.not.a.real.token"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_tampered_token_401(client):
    """A token with a corrupted signature → 401."""
    await _make_user(client, username="tamper", password="password1")
    token = await _login(client, "tamper", "password1")
    bad_token = token[:-5] + "XXXXX"  # corrupt last 5 chars of signature
    resp = await client.post(
        "/stations/",
        json={"name": "S", "location": "L"},
        headers={"Authorization": f"Bearer {bad_token}"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_empty_bearer_value_401(client):
    """Empty string as bearer value → 401."""
    resp = await client.get("/bikes/", headers={"Authorization": "Bearer "})
    # Bikes endpoint is public, so this doesn't trigger 401, but a protected one does
    resp2 = await client.post(
        "/stations/",
        json={"name": "S", "location": "L"},
        headers={"Authorization": "Bearer "},
    )
    assert resp2.status_code == 401


# ══════════════════════════════════════════════════════════
#  RENTALS – business rule enforcement
# ══════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_rental_nonexistent_bike_404(client):
    """Creating a rental with a non-existent bike → 404."""
    user = await _make_user(client, username="renter1", password="password1")
    resp = await client.post(f"/rentals/?user_id={user['id']}&bike_id=9999")
    assert resp.status_code == 404
    assert "Bike" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_rental_nonexistent_user_404(client):
    """Creating a rental with a non-existent user → 404."""
    bike = await _make_bike(client, battery=80)
    resp = await client.post(f"/rentals/?user_id=9999&bike_id={bike['id']}")
    assert resp.status_code == 404
    assert "User" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_rental_low_battery_rejected_400(client):
    """Bike with battery < 20 cannot be rented → 400."""
    user = await _make_user(client, username="renter2", password="password1")
    bike = await _make_bike(client, battery=10)
    resp = await client.post(f"/rentals/?user_id={user['id']}&bike_id={bike['id']}")
    assert resp.status_code == 400
    assert "battery" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_rental_battery_exactly_20_ok(client):
    """Bike with battery exactly 20 is at the boundary and should be rentable."""
    user = await _make_user(client, username="renter3", password="password1")
    bike = await _make_bike(client, battery=20)
    resp = await client.post(f"/rentals/?user_id={user['id']}&bike_id={bike['id']}")
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_rental_already_rented_bike_400(client):
    """Trying to rent a bike that is already rented → 400."""
    user1 = await _make_user(client, username="renter4", password="password1")
    user2 = await _make_user(client, username="renter5", password="password1")
    bike = await _make_bike(client, battery=80)

    # First rental succeeds
    await client.post(f"/rentals/?user_id={user1['id']}&bike_id={bike['id']}")
    # Second rental on same bike → rejected
    resp = await client.post(f"/rentals/?user_id={user2['id']}&bike_id={bike['id']}")
    assert resp.status_code == 400
    assert "rented" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_rental_full_lifecycle(client):
    """Create rental → bike becomes 'rented'; end rental → bike becomes 'available'."""
    user = await _make_user(client, username="lifecycle", password="password1")
    bike = await _make_bike(client, battery=80, status="available")

    # Create rental
    rental_resp = await client.post(f"/rentals/?user_id={user['id']}&bike_id={bike['id']}")
    assert rental_resp.status_code == 201
    rental_id = rental_resp.json()["id"]

    # Bike should now be "rented"
    bike_after = await client.get(f"/bikes/{bike['id']}")
    assert bike_after.json()["status"] == "rented"

    # End the rental
    end_resp = await client.post(f"/rentals/{rental_id}/end")
    assert end_resp.status_code == 200

    # Bike should be available again
    bike_final = await client.get(f"/bikes/{bike['id']}")
    assert bike_final.json()["status"] == "available"


@pytest.mark.asyncio
async def test_end_nonexistent_rental_404(client):
    """Ending a non-existent rental → 404."""
    resp = await client.post("/rentals/9999/end")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_rental_by_id_404(client):
    """GET /rentals/9999 → 404 when rental does not exist."""
    resp = await client.get("/rentals/9999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_rental_appears_in_list(client):
    """After creating a rental it shows up in GET /rentals/."""
    user = await _make_user(client, username="listcheck", password="password1")
    bike = await _make_bike(client, battery=60)
    rental = await client.post(f"/rentals/?user_id={user['id']}&bike_id={bike['id']}")
    rental_id = rental.json()["id"]

    resp = await client.get("/rentals/")
    assert resp.status_code == 200
    ids = [r["id"] for r in resp.json()]
    assert rental_id in ids
