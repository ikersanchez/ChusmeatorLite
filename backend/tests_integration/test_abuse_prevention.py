import pytest
from fastapi import status

def test_pin_rate_limiting(client):
    """Verify that a user cannot create more than 20 pins per day."""
    headers = {"X-User-Id": "rate_limited_pin_user"}
    
    # Create 20 pins
    for i in range(20):
        payload = {"lat": 40.0 + i*0.01, "lng": -3.0, "text": f"Pin {i}", "color": "blue"}
        response = client.post("/api/pins", json=payload, headers=headers)
        assert response.status_code == 201
        
    # Attempt to create the 21st pin
    payload = {"lat": 40.21, "lng": -3.0, "text": "Pin 21", "color": "blue"}
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
            "text": f"Area {i}",
            "fontSize": "16px"
        }
        response = client.post("/api/areas", json=payload, headers=headers)
        assert response.status_code == 201
        
    # Attempt to create the 21st area
    payload = {
        "latlngs": [[{"lat": 40.21, "lng": -3.0}, {"lat": 40.22, "lng": -3.0}, {"lat": 40.21, "lng": -2.99}]],
        "color": "blue",
        "text": "Area 21",
        "fontSize": "16px"
    }
    response = client.post("/api/areas", json=payload, headers=headers)
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]

def test_comment_rate_limiting(client):
    """Verify that a user cannot create more than 20 comments per day."""
    headers = {"X-User-Id": "rate_limited_comment_user"}
    
    # 1. Create a pin to comment on
    pin_payload = {"lat": 40.5, "lng": -3.5, "text": "Target Pin", "color": "red"}
    response = client.post("/api/pins", json=pin_payload, headers=headers)
    assert response.status_code == 201
    pin_id = response.json()["id"]
    
    # 2. Create 20 comments
    for i in range(20):
        comment_payload = {"text": f"Comment {i}"}
        response = client.post(f"/api/pins/{pin_id}/comments", json=comment_payload, headers=headers)
        assert response.status_code == 201
        
    # 3. Attempt to create the 21st comment
    comment_payload = {"text": "Comment 21"}
    response = client.post(f"/api/pins/{pin_id}/comments", json=comment_payload, headers=headers)
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]

def test_area_size_limit(client):
    """Verify that a user cannot create an area larger than 0.02 degrees."""
    headers = {"X-User-Id": "size_limited_user"}
    
    # Create an area that is too large (0.03 degrees wide)
    payload = {
        "latlngs": [[{"lat": 40.0, "lng": -3.0}, {"lat": 40.03, "lng": -3.0}, {"lat": 40.0, "lng": -2.97}]],
        "color": "blue",
        "text": "Huge Area",
        "fontSize": "16px"
    }
    response = client.post("/api/areas", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Area too large" in response.json()["detail"]
    
    # Create an area that is just within the limit (0.019 degrees wide)
    payload = {
        "latlngs": [[{"lat": 40.0, "lng": -3.0}, {"lat": 40.019, "lng": -3.0}, {"lat": 40.0, "lng": -2.981}]],
        "color": "blue",
        "text": "Large but OK Area",
        "fontSize": "16px"
    }
    response = client.post("/api/areas", json=payload, headers=headers)
    assert response.status_code == 201
