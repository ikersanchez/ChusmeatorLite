import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
import app.main as app_main
app_main.init_db = lambda: None  # Disable PG init during tests
from app.database import Base, get_db

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


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_get_user_id():
    response = client.get("/api/user")
    assert response.status_code == 200
    user_id = response.json()["userId"]
    assert user_id.startswith("user_")

    # Same client => same ID
    response = client.get("/api/user")
    assert response.status_code == 200
    assert response.json()["userId"] == user_id


def test_get_categories():
    response = client.get("/api/categories")
    assert response.status_code == 200
    cats = response.json()
    assert len(cats) == 10
    slugs = [c["slug"] for c in cats]
    assert "crime" in slugs
    assert "alcohol" in slugs
    assert all("label" in c and "icon" in c for c in cats)


def test_pin_crud_with_category():
    local_client = TestClient(app)

    # Create pin with category
    pin_data = {"lat": 40.0, "lng": -3.0, "category": "crime", "color": "red"}
    from app.schemas import PinCreate
    print("FIELDS:", PinCreate.model_fields.keys())
    response = local_client.post("/api/pins", json=pin_data)
    print(response.json())
    assert response.status_code == 201
    pin = response.json()
    assert pin["category"] == "crime"
    assert pin["color"] == "red"
    assert pin["originalColor"] == "red"
    pin_id = pin["id"]

    # Get map data
    response = local_client.get("/api/map-data")
    assert response.status_code == 200
    data = response.json()
    assert any(p["id"] == pin_id for p in data["pins"])
    found = next(p for p in data["pins"] if p["id"] == pin_id)
    assert found["category"] == "crime"
    assert found["voteColors"] == {"red": 0, "blue": 0, "green": 0}

    # Delete pin (unauthorized)
    other_client = TestClient(app)
    response = other_client.delete(f"/api/pins/{pin_id}")
    assert response.status_code == 403

    # Delete pin (authorized)
    response = local_client.delete(f"/api/pins/{pin_id}")
    assert response.status_code == 200
    assert response.json() == {"success": True}


def test_invalid_category():
    """Test that invalid category values are rejected."""
    pin_data = {"lat": 40.0, "lng": -3.0, "category": "nonexistent", "color": "blue"}
    response = client.post("/api/pins", json=pin_data)
    assert response.status_code == 422  # Validation error


def test_color_vote_on_pin():
    """Test the new color-based voting system."""
    local_client = TestClient(app)

    # Create a pin
    pin_data = {"lat": 40.0, "lng": -3.0, "category": "alcohol", "color": "blue"}
    response = local_client.post("/api/pins", json=pin_data)
    assert response.status_code == 201
    pin_id = response.json()["id"]

    # Vote green
    vote_data = {"targetType": "pin", "targetId": pin_id, "voteColor": "green"}
    response = local_client.post("/api/votes", json=vote_data)
    assert response.status_code == 201
    vote = response.json()
    assert vote["targetType"] == "pin"
    assert vote["voteColor"] == "green"

    # Check map-data
    response = local_client.get("/api/map-data")
    data = response.json()
    found = next(p for p in data["pins"] if p["id"] == pin_id)
    assert found["voteColors"]["green"] == 1
    assert found["userVoteColor"] == "green"

    # Vote same color again => toggles off (removes vote)
    response = local_client.post("/api/votes", json=vote_data)
    assert response.status_code == 200  # Vote removed

    # Check map-data => no votes
    response = local_client.get("/api/map-data")
    data = response.json()
    found = next(p for p in data["pins"] if p["id"] == pin_id)
    assert found["voteColors"]["green"] == 0
    assert found["userVoteColor"] is None


def test_switch_vote_color():
    """Test switching from one color to another."""
    local_client = TestClient(app)

    pin_data = {"lat": 41.0, "lng": -4.0, "category": "traffic", "color": "blue"}
    response = local_client.post("/api/pins", json=pin_data)
    pin_id = response.json()["id"]

    # Vote red
    local_client.post("/api/votes", json={"targetType": "pin", "targetId": pin_id, "voteColor": "red"})

    # Verify red
    data = local_client.get("/api/map-data").json()
    pin = next(p for p in data["pins"] if p["id"] == pin_id)
    assert pin["voteColors"]["red"] == 1
    assert pin["userVoteColor"] == "red"

    # Switch to green
    response = local_client.post("/api/votes", json={"targetType": "pin", "targetId": pin_id, "voteColor": "green"})
    assert response.status_code == 201

    # Verify green, red removed
    data = local_client.get("/api/map-data").json()
    pin = next(p for p in data["pins"] if p["id"] == pin_id)
    assert pin["voteColors"]["green"] == 1
    assert pin["voteColors"]["red"] == 0
    assert pin["userVoteColor"] == "green"


def test_multi_user_color_voting():
    """Test that votes from multiple users aggregate correctly."""
    c1 = TestClient(app)
    c2 = TestClient(app)
    c3 = TestClient(app)

    # Create pin with blue color
    pin_data = {"lat": 42.0, "lng": -5.0, "category": "dirty", "color": "blue"}
    response = c1.post("/api/pins", json=pin_data)
    pin_id = response.json()["id"]

    # c1 votes green, c2 votes green, c3 votes red
    c1.post("/api/votes", json={"targetType": "pin", "targetId": pin_id, "voteColor": "green"})
    c2.post("/api/votes", json={"targetType": "pin", "targetId": pin_id, "voteColor": "green"})
    c3.post("/api/votes", json={"targetType": "pin", "targetId": pin_id, "voteColor": "red"})

    data = c1.get("/api/map-data").json()
    pin = next(p for p in data["pins"] if p["id"] == pin_id)
    assert pin["voteColors"]["green"] == 2
    assert pin["voteColors"]["red"] == 1
    assert pin["voteColors"]["blue"] == 0
    assert pin["userVoteColor"] == "green"

    # c3 should see their vote color
    data = c3.get("/api/map-data").json()
    pin = next(p for p in data["pins"] if p["id"] == pin_id)
    assert pin["userVoteColor"] == "red"


def test_vote_on_area():
    """Test color voting on an area."""
    local_client = TestClient(app)
    area_data = {
        "latlngs": [[{"lat": 40.0, "lng": -3.0}, {"lat": 40.01, "lng": -3.0}, {"lat": 40.01, "lng": -2.99}]],
        "color": "blue",
        "category": "construction",
        "fontSize": "14px"
    }
    response = local_client.post("/api/areas", json=area_data)
    assert response.status_code == 201
    area_id = response.json()["id"]

    # Vote red
    response = local_client.post("/api/votes", json={"targetType": "area", "targetId": area_id, "voteColor": "red"})
    assert response.status_code == 201

    # Check map-data
    data = local_client.get("/api/map-data").json()
    area = next(a for a in data["areas"] if a["id"] == area_id)
    assert area["voteColors"]["red"] == 1
    assert area["userVoteColor"] == "red"


def test_vote_nonexistent_target():
    response = client.post("/api/votes", json={"targetType": "pin", "targetId": 999999, "voteColor": "red"})
    assert response.status_code == 404


def test_unvote():
    """Test removing a vote."""
    local_client = TestClient(app)

    pin_data = {"lat": 40.0, "lng": -3.0, "category": "crime", "color": "red"}
    response = local_client.post("/api/pins", json=pin_data)
    pin_id = response.json()["id"]

    # Vote
    local_client.post("/api/votes", json={"targetType": "pin", "targetId": pin_id, "voteColor": "green"})

    # Unvote
    response = local_client.delete(f"/api/votes/pin/{pin_id}")
    assert response.status_code == 200

    # Verify removed
    data = local_client.get("/api/map-data").json()
    pin = next(p for p in data["pins"] if p["id"] == pin_id)
    assert pin["voteColors"]["green"] == 0
    assert pin["userVoteColor"] is None
