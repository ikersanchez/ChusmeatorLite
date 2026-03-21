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

def test_categories_endpoint(client):
    """Verify the categories listing endpoint."""
    response = client.get("/api/categories")
    assert response.status_code == 200
    cats = response.json()
    assert len(cats) == 10
    assert all("slug" in c and "label" in c and "icon" in c for c in cats)

def test_pin_crud_flow(client):
    """Full CRUD lifecycle for Pins with categories."""
    headers = {"X-User-Id": "pin_user"}
    
    # 1. Create
    payload = {"lat": 40.4168, "lng": -3.7038, "category": "crime", "color": "green"}
    response = client.post("/api/pins", json=payload, headers=headers)
    assert response.status_code == 201
    pin = response.json()
    assert pin["category"] == "crime"
    assert pin["color"] == "green"
    assert pin["originalColor"] == "green"
    pin_id = pin["id"]

    # 2. Read (via map-data)
    response = client.get("/api/map-data", headers=headers)
    assert response.status_code == 200
    data = response.json()
    found = next((p for p in data["pins"] if p["id"] == pin_id), None)
    assert found is not None
    assert found["category"] == "crime"
    assert found["voteColors"] == {"red": 0, "blue": 0, "green": 0}

    # 3. Delete (unauthorized)
    response = client.delete(f"/api/pins/{pin_id}", headers={"X-User-Id": "thief"})
    assert response.status_code == 403

    # 4. Delete (authorized)
    response = client.delete(f"/api/pins/{pin_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_area_crud_flow(client):
    """Full CRUD lifecycle for Areas with categories."""
    headers = {"X-User-Id": "area_user"}
    
    # 1. Create
    payload = {
        "latlngs": [[{"lat": 40.4, "lng": -3.7}, {"lat": 40.41, "lng": -3.7}, {"lat": 40.4, "lng": -3.69}]],
        "color": "blue",
        "category": "loud_music",
        "fontSize": "16px"
    }
    response = client.post("/api/areas", json=payload, headers=headers)
    assert response.status_code == 201
    area = response.json()
    assert area["category"] == "loud_music"
    area_id = area["id"]

    # 2. Delete
    response = client.delete(f"/api/areas/{area_id}", headers=headers)
    assert response.status_code == 200

def test_color_vote_flow(client):
    """Test color-based voting on a pin."""
    headers = {"X-User-Id": "voter_user"}

    # Create a pin
    pin_resp = client.post("/api/pins", json={"lat": 40.0, "lng": -3.0, "category": "alcohol", "color": "blue"}, headers=headers)
    pin_id = pin_resp.json()["id"]

    # Vote green
    vote_resp = client.post("/api/votes", json={"targetType": "pin", "targetId": pin_id, "voteColor": "green"}, headers=headers)
    assert vote_resp.status_code == 201
    assert vote_resp.json()["voteColor"] == "green"

    # Verify in map-data
    data = client.get("/api/map-data", headers=headers).json()
    pin = next(p for p in data["pins"] if p["id"] == pin_id)
    assert pin["voteColors"]["green"] == 1
    assert pin["userVoteColor"] == "green"

    # Unvote
    del_resp = client.delete(f"/api/votes/pin/{pin_id}", headers=headers)
    assert del_resp.status_code == 200


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
