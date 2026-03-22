import pytest
from app.database_layer.models import Bike 


@pytest.mark.asyncio
async def test_get_bikes(client):
    resp = await client.get("/bikes/")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_bikes_returns_inserted_bike(client, test_db_session):
    bike = Bike(model="TestBike", battery=99, status="available") 
    test_db_session.add(bike)
    await test_db_session.commit()

    resp = await client.get("/bikes/")
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["model"] == "TestBike" 
    assert data[0]["battery_level"] == 99
    assert data[0]["status"] == "available" 
    

@pytest.mark.asyncio
async def test_get_bike_by_id_404(client):
    resp = await client.get("/bikes/9999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Bike not found"



@pytest.mark.asyncio
async def test_delete_bike_success(client, test_db_session):
    bike = Bike(model="DeleteMe", battery=10, status="available")
    test_db_session.add(bike)
    await test_db_session.commit()
    await test_db_session.refresh(bike)

    resp = await client.delete(f"/bikes/{bike.id}")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Bike deleted"

    # verify it's gone
    resp2 = await client.get(f"/bikes/{bike.id}")
    assert resp2.status_code == 404