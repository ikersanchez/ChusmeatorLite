import pytest
from fastapi import status

def test_pin_rate_limiting(client):
    """Verify that a user cannot create more than 20 pins per day."""
    headers = {"X-User-Id": "rate_limited_pin_user"}
    
    # Create 20 pins
    for i in range(20):
        payload = {"lat": 40.0 + i*0.01, "lng": -3.0, "category": "crime", "color": "blue"}
        response = client.post("/api/pins", json=payload, headers=headers)
        assert response.status_code == 201
        
    # Attempt to create the 21st pin
    payload = {"lat": 40.21, "lng": -3.0, "category": "crime", "color": "blue"}
    response = client.post("/api/pins", json=payload, headers=headers)
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]

def test_area_rate_limiting(client):
    """Verify that a user cannot create more than 20 areas per day."""
    headers = {"X-User-Id": "rate_limited_area_user"}
    
    # Create 20 areas
    for i in range(20):
        payload = {
            "latlngs": [[{"lat": 40.0 + i*0.01, "lng": -3.0}, {"lat": 40.01 + i*0.01, "lng": -3.0}, {"lat": 40.0 + i*0.01, "lng": -2.99}]],
            "color": "blue",
            "category": "construction",
            "fontSize": "16px"
        }
        response = client.post("/api/areas", json=payload, headers=headers)
        assert response.status_code == 201
        
    # Attempt to create the 21st area
    payload = {
        "latlngs": [[{"lat": 40.21, "lng": -3.0}, {"lat": 40.22, "lng": -3.0}, {"lat": 40.21, "lng": -2.99}]],
        "color": "blue",
        "category": "construction",
        "fontSize": "16px"
    }
    response = client.post("/api/areas", json=payload, headers=headers)
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]

def test_area_size_limit(client):
    """Verify that a user cannot create an area larger than 0.02 degrees."""
    headers = {"X-User-Id": "size_limited_user"}
    
    # Create an area that is too large (0.03 degrees wide)
    payload = {
        "latlngs": [[{"lat": 40.0, "lng": -3.0}, {"lat": 40.03, "lng": -3.0}, {"lat": 40.0, "lng": -2.97}]],
        "color": "blue",
        "category": "loud_music",
        "fontSize": "16px"
    }
    response = client.post("/api/areas", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Area too large" in response.json()["detail"]
    
    # Create an area that is just within the limit (0.019 degrees wide)
    payload = {
        "latlngs": [[{"lat": 40.0, "lng": -3.0}, {"lat": 40.019, "lng": -3.0}, {"lat": 40.0, "lng": -2.981}]],
        "color": "blue",
        "category": "loud_music",
        "fontSize": "16px"
    }
    response = client.post("/api/areas", json=payload, headers=headers)
    assert response.status_code == 201
