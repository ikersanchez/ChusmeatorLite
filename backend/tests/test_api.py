import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.services.moderation_service import ModerationService
import pytest_asyncio

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_moderation(monkeypatch):
    """Mocks ModerationService to block tests with 'PII' and allow everything else."""
    async def mock_check_text(text: str):
        if "PII" in text:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Text contains Personal Identifiable Information (PII) and cannot be saved.")
    monkeypatch.setattr(ModerationService, "check_text_for_pii", mock_check_text)
    
@pytest.fixture(autouse=True)
def auto_mock_moderation(mock_moderation):
    """Automatically mock moderation for all tests unless overridden."""
    pass

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_get_user_id():
    # First call should generate a user ID
    response = client.get("/api/user")
    assert response.status_code == 200
    user_id = response.json()["userId"]
    assert user_id.startswith("user_")
    
    # Second call with the same client (and thus same cookies) should return the same ID
    response = client.get("/api/user")
    assert response.status_code == 200
    assert response.json()["userId"] == user_id

def test_pin_crud():
    # Use a fresh client for this test
    local_client = TestClient(app)
    
    # Create pin
    pin_data = {"lat": 40.0, "lng": -3.0, "text": "Test Pin", "color": "red"}
    response = local_client.post("/api/pins", json=pin_data)
    assert response.status_code == 201
    pin = response.json()
    assert pin["text"] == "Test Pin"
    pin_id = pin["id"]
    user_id = pin["userId"]
    
    # Get map data
    response = local_client.get("/api/map-data")
    assert response.status_code == 200
    data = response.json()
    assert any(p["id"] == pin_id for p in data["pins"])
    
    # Delete pin (unauthorized - different client/user)
    other_client = TestClient(app)
    response = other_client.delete(f"/api/pins/{pin_id}")
    assert response.status_code == 403
    
    # Delete pin (authorized)
    response = local_client.delete(f"/api/pins/{pin_id}")
    assert response.status_code == 200
    assert response.json() == {"success": True}



def test_vote_on_pin():
    local_client = TestClient(app)
    
    # Create a pin to vote on
    pin_data = {"lat": 40.0, "lng": -3.0, "text": "Votable Pin"}
    response = local_client.post("/api/pins", json=pin_data)
    assert response.status_code == 201
    pin_id = response.json()["id"]

    # Vote on pin (like)
    vote_data = {"targetType": "pin", "targetId": pin_id, "value": 1}
    response = local_client.post("/api/votes", json=vote_data)
    assert response.status_code == 201
    vote = response.json()
    assert vote["targetType"] == "pin"
    assert vote["value"] == 1

    # Verify vote count in map-data
    response = local_client.get("/api/map-data")
    assert response.status_code == 200
    data = response.json()
    voted_pin = next(p for p in data["pins"] if p["id"] == pin_id)
    assert voted_pin["votes"] == 1
    assert voted_pin["userVoteValue"] == 1

    # Duplicate vote should fail with 409
    response = local_client.post("/api/votes", json=vote_data)
    assert response.status_code == 409

    # Another user should see userVoteValue=0
    other_client = TestClient(app)
    response = other_client.get("/api/map-data")
    data = response.json()
    voted_pin = next(p for p in data["pins"] if p["id"] == pin_id)
    assert voted_pin["votes"] == 1
    assert voted_pin["userVoteValue"] == 0

    # Unvote
    response = local_client.delete(f"/api/votes/pin/{pin_id}")
    assert response.status_code == 200

    # Verify vote removed
    response = local_client.get("/api/map-data")
    data = response.json()
    voted_pin = next(p for p in data["pins"] if p["id"] == pin_id)
    assert voted_pin["votes"] == 0
    assert voted_pin["userVoteValue"] == 0

def test_vote_on_area():
    local_client = TestClient(app)
    # Create an area
    area_data = {
        "latlngs": [[40.0, -3.0], [40.01, -3.0], [40.01, -2.99]],
        "color": "blue",
        "text": "Test Area",
        "fontSize": "14px"
    }
    response = local_client.post("/api/areas", json=area_data)
    assert response.status_code == 201
    area_id = response.json()["id"]

    # Vote (like)
    response = local_client.post("/api/votes", json={"targetType": "area", "targetId": area_id, "value": 1})
    assert response.status_code == 201

    # Check map-data
    response = local_client.get("/api/map-data")
    data = response.json()
    area = next(a for a in data["areas"] if a["id"] == area_id)
    assert area["votes"] == 1
    assert area["userVoteValue"] == 1

def test_vote_on_nonexistent_target():
    response = client.post("/api/votes", json={"targetType": "pin", "targetId": 999999999, "value": 1})
    assert response.status_code == 404

def test_vote_on_area_new():
    """Test voting on an area."""
    local_client = TestClient(app)
    # Create an area first
    area_data = {
        "latlngs": [{"lat": 40.7, "lng": -74.0}],
        "color": "green",
        "text": "Voting Area",
        "fontSize": "large"
    }
    area_resp = local_client.post("/api/areas", json=area_data)
    area_id = area_resp.json()["id"]

    # Vote on the area (like)
    vote_data = {
        "targetType": "area",
        "targetId": area_id,
        "value": 1
    }
    resp = local_client.post("/api/votes", json=vote_data)
    assert resp.status_code == 201
    
    # Check that map data reflects the vote
    map_resp = local_client.get("/api/map-data")
    area = next(a for a in map_resp.json()["areas"] if a["id"] == area_id)
    assert area["votes"] == 1
    assert area["userVoteValue"] == 1


def test_dislike_on_pin():
    """Test disliking a pin (negative vote)."""
    local_client = TestClient(app)
    
    # Create a pin
    pin_data = {"lat": 40.0, "lng": -3.0, "text": "Dislikable Pin"}
    response = local_client.post("/api/pins", json=pin_data)
    assert response.status_code == 201
    pin_id = response.json()["id"]

    # Dislike the pin
    vote_data = {"targetType": "pin", "targetId": pin_id, "value": -1}
    response = local_client.post("/api/votes", json=vote_data)
    assert response.status_code == 201
    assert response.json()["value"] == -1

    # Verify negative vote count
    response = local_client.get("/api/map-data")
    data = response.json()
    pin = next(p for p in data["pins"] if p["id"] == pin_id)
    assert pin["votes"] == -1
    assert pin["userVoteValue"] == -1

    # Undislike
    response = local_client.delete(f"/api/votes/pin/{pin_id}")
    assert response.status_code == 200

    # Verify vote removed
    response = local_client.get("/api/map-data")
    data = response.json()
    pin = next(p for p in data["pins"] if p["id"] == pin_id)
    assert pin["votes"] == 0
    assert pin["userVoteValue"] == 0


def test_like_then_switch_to_dislike():
    """Test switching from like to dislike (requires unvote + revote)."""
    local_client = TestClient(app)
    
    # Create a pin
    pin_data = {"lat": 41.0, "lng": -4.0, "text": "Switchable Pin"}
    response = local_client.post("/api/pins", json=pin_data)
    assert response.status_code == 201
    pin_id = response.json()["id"]

    # Like the pin
    response = local_client.post("/api/votes", json={"targetType": "pin", "targetId": pin_id, "value": 1})
    assert response.status_code == 201

    # Verify like
    response = local_client.get("/api/map-data")
    pin = next(p for p in response.json()["pins"] if p["id"] == pin_id)
    assert pin["votes"] == 1
    assert pin["userVoteValue"] == 1

    # Unvote first, then dislike (simulates frontend behavior)
    response = local_client.delete(f"/api/votes/pin/{pin_id}")
    assert response.status_code == 200

    response = local_client.post("/api/votes", json={"targetType": "pin", "targetId": pin_id, "value": -1})
    assert response.status_code == 201

    # Verify dislike
    response = local_client.get("/api/map-data")
    pin = next(p for p in response.json()["pins"] if p["id"] == pin_id)
    assert pin["votes"] == -1
    assert pin["userVoteValue"] == -1


def test_multiple_users_voting():
    """Test that likes and dislikes from multiple users sum correctly."""
    client1 = TestClient(app)
    client2 = TestClient(app)
    client3 = TestClient(app)

    # Create a pin
    pin_data = {"lat": 42.0, "lng": -5.0, "text": "Multi-vote Pin"}
    response = client1.post("/api/pins", json=pin_data)
    assert response.status_code == 201
    pin_id = response.json()["id"]

    # User 1 likes
    response = client1.post("/api/votes", json={"targetType": "pin", "targetId": pin_id, "value": 1})
    assert response.status_code == 201

    # User 2 likes
    response = client2.post("/api/votes", json={"targetType": "pin", "targetId": pin_id, "value": 1})
    assert response.status_code == 201

    # User 3 dislikes
    response = client3.post("/api/votes", json={"targetType": "pin", "targetId": pin_id, "value": -1})
    assert response.status_code == 201

    # Total should be 1 + 1 + (-1) = 1
    response = client1.get("/api/map-data")
    pin = next(p for p in response.json()["pins"] if p["id"] == pin_id)
    assert pin["votes"] == 1
    assert pin["userVoteValue"] == 1  # User 1 liked

    # User 3 should see their dislike
    response = client3.get("/api/map-data")
    pin = next(p for p in response.json()["pins"] if p["id"] == pin_id)
    assert pin["votes"] == 1
    assert pin["userVoteValue"] == -1  # User 3 disliked


def test_pin_comments():
    """Test creating and getting comments for a pin."""
    local_client = TestClient(app)
    # Create a pin first
    pin_data = {
        "lat": 40.0,
        "lng": -70.0,
        "text": "Pin for comments",
        "color": "blue"
    }
    pin_resp = local_client.post("/api/pins", json=pin_data)
    assert pin_resp.status_code == 201
    pin_id = pin_resp.json()["id"]

    # Add a comment
    comment_data = {"text": "This is a great pin!"}
    resp = local_client.post(f"/api/pins/{pin_id}/comments", json=comment_data)
    assert resp.status_code == 201
    data = resp.json()
    assert data["text"] == comment_data["text"]
    assert data["targetType"] == "pin"
    assert data["targetId"] == pin_id
    
    # Get comments
    get_resp = local_client.get(f"/api/pins/{pin_id}/comments")
    assert get_resp.status_code == 200
    comments_list = get_resp.json()
    assert len(comments_list) == 1

def test_pin_comment_validation():
    """Test that comment text cannot exceed 100 characters."""
    # Create a pin
    pin_data = {
        "lat": 40.0,
        "lng": -70.0,
        "text": "Pin for validation",
        "color": "blue"
    }
    pin_resp = client.post("/api/pins", json=pin_data)
    pin_id = pin_resp.json()["id"]

    # Add comment with >100 characters
    long_text = "a" * 101
    comment_data = {"text": long_text}
    resp = client.post(f"/api/pins/{pin_id}/comments", json=comment_data)
    assert resp.status_code == 422  # Unprocessable Entity (validation error)

def test_area_comments():
    """Test creating and getting comments for an area."""
    local_client = TestClient(app)
    # Create an area first
    area_data = {
        "latlngs": [[40.0, -3.0], [40.01, -3.0], [40.01, -2.99]],
        "color": "blue",
        "text": "Area for comments",
        "fontSize": "14px"
    }
    area_resp = local_client.post("/api/areas", json=area_data)
    assert area_resp.status_code == 201
    area_id = area_resp.json()["id"]

    # Add a comment
    comment_data = {"text": "This area is awesome!"}
    resp = local_client.post(f"/api/areas/{area_id}/comments", json=comment_data)
    assert resp.status_code == 201
    data = resp.json()
    assert data["text"] == comment_data["text"]
    assert data["targetType"] == "area"
    assert data["targetId"] == area_id

    # Get comments
    get_resp = local_client.get(f"/api/areas/{area_id}/comments")
    assert get_resp.status_code == 200
    comments_list = get_resp.json()
    assert len(comments_list) == 1

def test_area_comment_validation():
    """Test that area comment text cannot exceed 100 characters."""
    local_client = TestClient(app)
    area_data = {
        "latlngs": [[40.0, -3.0], [40.01, -3.0], [40.01, -2.99]],
        "color": "green",
        "text": "Area for validation",
        "fontSize": "14px"
    }
    area_resp = local_client.post("/api/areas", json=area_data)
    area_id = area_resp.json()["id"]

    # Add comment with >100 characters
    long_text = "a" * 101
    comment_data = {"text": long_text}
    resp = local_client.post(f"/api/areas/{area_id}/comments", json=comment_data)
    assert resp.status_code == 422  # Unprocessable Entity (validation error)

def test_area_comment_nonexistent():
    """Test commenting on non-existent area returns 404."""
    resp = client.post("/api/areas/999999/comments", json={"text": "Hello"})
    assert resp.status_code == 404

def test_pin_text_validation():
    """Test that pin text cannot exceed 100 characters."""
    pin_data = {
        "lat": 40.0,
        "lng": -70.0,
        "text": "a" * 101,
        "color": "blue"
    }
    resp = client.post("/api/pins", json=pin_data)
    assert resp.status_code == 422

def test_moderation_blocks_pii_pin():
    """Test that creating a pin with PII is blocked."""
    pin_data = {
        "lat": 40.0,
        "lng": -70.0,
        "text": "Call me at PII number",
        "color": "blue"
    }
    resp = client.post("/api/pins", json=pin_data)
    assert resp.status_code == 400
    assert "PII" in resp.json()["detail"]

def test_moderation_blocks_pii_area():
    """Test that creating an area with PII is blocked."""
    area_data = {
        "latlngs": [[40.0, -3.0], [40.01, -3.0], [40.01, -2.99]],
        "color": "blue",
        "text": "This is PII text",
        "fontSize": "14px"
    }
    resp = client.post("/api/areas", json=area_data)
    assert resp.status_code == 400
    assert "PII" in resp.json()["detail"]

def test_moderation_blocks_pii_comment():
    """Test that creating a comment with PII is blocked."""
    local_client = TestClient(app)
    # Create valid pin
    pin_data = {"lat": 40.0, "lng": -70.0, "text": "Valid Pin", "color": "blue"}
    pin_resp = local_client.post("/api/pins", json=pin_data)
    assert pin_resp.status_code == 201
    pin_id = pin_resp.json()["id"]

    # Block comment with PII
    comment_data = {"text": "My phone is PII"}
    resp = local_client.post(f"/api/pins/{pin_id}/comments", json=comment_data)
    assert resp.status_code == 400
    assert "PII" in resp.json()["detail"]
