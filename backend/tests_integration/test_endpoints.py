import pytest

def test_health_check(client):
    """Verify the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_user_flow(client):
    """Verify user ID retrieval."""
    headers = {"X-User-Id": "integration_tester"}
    response = client.get("/api/user", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"userId": "integration_tester"}

def test_pin_crud_flow(client):
    """Full CRUD lifecycle for Pins."""
    headers = {"X-User-Id": "pin_user"}
    
    # 1. Create
    payload = {"lat": 40.4168, "lng": -3.7038, "text": "Plaza Mayor", "color": "green"}
    response = client.post("/api/pins", json=payload, headers=headers)
    assert response.status_code == 201
    pin = response.json()
    assert pin["text"] == "Plaza Mayor"
    assert pin["color"] == "green"
    pin_id = pin["id"]

    # 2. Read (via map-data)
    response = client.get("/api/map-data", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert any(p["id"] == pin_id for p in data["pins"])

    # 3. Delete (unauthorized)
    response = client.delete(f"/api/pins/{pin_id}", headers={"X-User-Id": "thief"})
    assert response.status_code == 403

    # 4. Delete (authorized)
    response = client.delete(f"/api/pins/{pin_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_area_crud_flow(client):
    """Full CRUD lifecycle for Areas."""
    headers = {"X-User-Id": "area_user"}
    
    # 1. Create
    payload = {
        "latlngs": [[{"lat": 40.4, "lng": -3.7}, {"lat": 40.5, "lng": -3.7}, {"lat": 40.4, "lng": -3.6}]],
        "color": "blue",
        "text": "Neighborhood A",
        "fontSize": "16px"
    }
    response = client.post("/api/areas", json=payload, headers=headers)
    assert response.status_code == 201
    area = response.json()
    area_id = area["id"]

    # 2. Delete
    response = client.delete(f"/api/areas/{area_id}", headers=headers)
    assert response.status_code == 200



from unittest.mock import patch, AsyncMock

def test_search_proxy(client):
    """Verify the search proxy endpoint mocking LocationIQ to prevent API calls."""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: [
        {"lat": "40.4168", "lon": "-3.7038", "display_name": "Madrid, Spain"}
    ]
    # raise_for_status should do nothing
    mock_response.raise_for_status = lambda: None
    
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        response = client.get("/api/search?q=Madrid")
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)
        assert len(results) == 1
        assert "lat" in results[0]
        assert "lon" in results[0]
        assert "display_name" in results[0]
