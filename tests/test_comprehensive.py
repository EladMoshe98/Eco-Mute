"""
Comprehensive tests covering: users, stations, auth, and input validation.
All tests use the in-memory SQLite fixture from conftest.py.
"""
import pytest


# ─────────────────────────── USERS ───────────────────────────

@pytest.mark.asyncio
async def test_get_all_users_empty(client):
    """GET /users/ returns empty list when no users exist."""
    resp = await client.get("/users/")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_user_success(client):
    """POST /users/ creates a user and returns id, username, is_active."""
    payload = {"username": "alice", "email": "alice@test.com", "password": "secret123", "role": "user"}
    resp = await client.post("/users/", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "alice"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_create_user_appears_in_list(client):
    """After creating a user it should appear in GET /users/."""
    await client.post("/users/", json={"username": "bob", "email": "bob@test.com", "password": "password1", "role": "user"})
    resp = await client.get("/users/")
    assert resp.status_code == 200
    usernames = [u["username"] for u in resp.json()]
    assert "bob" in usernames


@pytest.mark.asyncio
async def test_get_user_by_id_success(client):
    """GET /users/{id} returns the correct user."""
    create = await client.post("/users/", json={"username": "carol", "email": "carol@test.com", "password": "password1", "role": "user"})
    user_id = create.json()["id"]
    resp = await client.get(f"/users/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["username"] == "carol"


@pytest.mark.asyncio
async def test_get_user_by_id_404(client):
    """GET /users/9999 returns 404 when user does not exist."""
    resp = await client.get("/users/9999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_create_user_duplicate_username_409(client):
    """Creating two users with the same username returns 409."""
    payload = {"username": "dave", "email": "dave@test.com", "password": "password1", "role": "user"}
    await client.post("/users/", json=payload)
    resp = await client.post("/users/", json={**payload, "email": "dave2@test.com"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_user_duplicate_email_409(client):
    """Creating two users with the same email returns 409."""
    await client.post("/users/", json={"username": "eve1", "email": "shared@test.com", "password": "password1", "role": "user"})
    resp = await client.post("/users/", json={"username": "eve2", "email": "shared@test.com", "password": "password1", "role": "user"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_user_short_password_422(client):
    """Password shorter than 8 characters is rejected with 422."""
    resp = await client.post("/users/", json={"username": "frank", "email": "frank@test.com", "password": "short", "role": "user"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_user_invalid_email_422(client):
    """Invalid email format is rejected with 422."""
    resp = await client.post("/users/", json={"username": "grace", "email": "not-an-email", "password": "password1", "role": "user"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_delete_user_success(client):
    """DELETE /users/{id} removes the user."""
    create = await client.post("/users/", json={"username": "henry", "email": "henry@test.com", "password": "password1", "role": "user"})
    user_id = create.json()["id"]
    resp = await client.delete(f"/users/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["message"] == "User deleted"
    # Confirm it's gone
    assert (await client.get(f"/users/{user_id}")).status_code == 404


@pytest.mark.asyncio
async def test_delete_user_404(client):
    """DELETE /users/9999 returns 404 when user does not exist."""
    resp = await client.delete("/users/9999")
    assert resp.status_code == 404


# ─────────────────────────── AUTH ───────────────────────────

async def _create_and_login(client, username="testuser", password="testpass1", role="user"):
    """Helper: create a user, log in, return the bearer token."""
    await client.post("/users/", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": password,
        "role": role,
    })
    resp = await client.post("/auth/token", data={"username": username, "password": password})
    return resp


@pytest.mark.asyncio
async def test_login_success(client):
    """Valid credentials return an access_token."""
    resp = await _create_and_login(client)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password_401(client):
    """Wrong password returns 401."""
    await client.post("/users/", json={"username": "ian", "email": "ian@test.com", "password": "correctpass", "role": "user"})
    resp = await client.post("/auth/token", data={"username": "ian", "password": "wrongpass"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user_401(client):
    """Non-existent username returns 401."""
    resp = await client.post("/auth/token", data={"username": "ghost", "password": "password1"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_token_401(client):
    """Calling an admin-protected endpoint without a token returns 401."""
    resp = await client.post("/stations/", json={"name": "S1", "location": "Loc1"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_non_admin_403(client):
    """A regular user calling an admin-protected endpoint gets 403."""
    login = await _create_and_login(client, username="regular", password="password1", role="user")
    token = login.json()["access_token"]
    resp = await client.post(
        "/stations/",
        json={"name": "S1", "location": "Loc1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


# ─────────────────────────── STATIONS ───────────────────────────

async def _admin_token(client):
    """Helper: create an admin user and return bearer token."""
    login = await _create_and_login(client, username="admin_user", password="adminpass1", role="admin")
    return login.json()["access_token"]


@pytest.mark.asyncio
async def test_get_stations_empty(client):
    """GET /stations/ returns empty list initially."""
    resp = await client.get("/stations/")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_station_as_admin(client):
    """Admin can POST /stations/ and it appears in the list."""
    token = await _admin_token(client)
    resp = await client.post(
        "/stations/",
        json={"name": "Central", "location": "Downtown"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Central"
    assert data["location"] == "Downtown"
    assert "id" in data


@pytest.mark.asyncio
async def test_station_appears_in_list_after_create(client):
    """Station created by admin shows up in GET /stations/."""
    token = await _admin_token(client)
    await client.post(
        "/stations/",
        json={"name": "North", "location": "North District"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get("/stations/")
    names = [s["name"] for s in resp.json()]
    assert "North" in names


@pytest.mark.asyncio
async def test_delete_station_as_admin(client):
    """Admin can DELETE /stations/{id}."""
    token = await _admin_token(client)
    create = await client.post(
        "/stations/",
        json={"name": "TempStation", "location": "Somewhere"},
        headers={"Authorization": f"Bearer {token}"},
    )
    station_id = create.json()["id"]
    resp = await client.delete(f"/stations/{station_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Station deleted"


@pytest.mark.asyncio
async def test_delete_station_404(client):
    """DELETE /stations/9999 returns 404 when station does not exist."""
    token = await _admin_token(client)
    resp = await client.delete("/stations/9999", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


# ─────────────────────────── BIKES - INPUT VALIDATION ───────────────────────────

@pytest.mark.asyncio
async def test_create_bike_battery_above_100_rejected(client):
    """Battery level > 100 is rejected with 422."""
    resp = await client.post("/bikes/", json={"model": "X", "battery_level": 150, "status": "available"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_bike_negative_battery_rejected(client):
    """Negative battery level is rejected with 422."""
    resp = await client.post("/bikes/", json={"model": "X", "battery_level": -5, "status": "available"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_bike_invalid_status_rejected(client):
    """Invalid status value is rejected with 422."""
    resp = await client.post("/bikes/", json={"model": "X", "battery_level": 80, "status": "broken"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_bike_success(client):
    """Valid bike creation returns the bike with correct fields."""
    resp = await client.post("/bikes/", json={"model": "Trek", "battery_level": 75, "status": "available"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["model"] == "Trek"
    assert data["battery_level"] == 75
    assert data["status"] == "available"


@pytest.mark.asyncio
async def test_update_bike_success(client):
    """PUT /bikes/{id} updates an existing bike."""
    create = await client.post("/bikes/", json={"model": "OldModel", "battery_level": 50, "status": "available"})
    bike_id = create.json()["id"]
    resp = await client.put(f"/bikes/{bike_id}", json={"model": "NewModel", "battery_level": 90, "status": "maintenance"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["model"] == "NewModel"
    assert data["battery_level"] == 90
    assert data["status"] == "maintenance"


@pytest.mark.asyncio
async def test_update_bike_404(client):
    """PUT /bikes/9999 returns 404 when bike does not exist."""
    resp = await client.put("/bikes/9999", json={"model": "X", "battery_level": 50, "status": "available"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_bikes_filter_by_status(client):
    """GET /bikes/?status=available filters correctly."""
    await client.post("/bikes/", json={"model": "A", "battery_level": 80, "status": "available"})
    await client.post("/bikes/", json={"model": "B", "battery_level": 60, "status": "maintenance"})

    resp = await client.get("/bikes/?status=available")
    assert resp.status_code == 200
    bikes = resp.json()
    assert all(b["status"] == "available" for b in bikes)
    assert len(bikes) == 1
