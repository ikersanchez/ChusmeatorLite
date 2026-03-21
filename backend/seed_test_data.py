"""Seed script to create fake pins and areas with votes for testing."""
import httpx
import time

BASE = "http://localhost:8000/api"

# Fake users for voting
USERS = [f"seed_user_{i}" for i in range(1, 11)]


def api(method, path, user_id, json=None):
    headers = {"X-User-Id": user_id, "Content-Type": "application/json"}
    r = httpx.request(method, f"{BASE}{path}", headers=headers, json=json, timeout=10)
    r.raise_for_status()
    return r.json() if r.status_code != 204 else None


def vote(user_id, target_type, target_id):
    try:
        api("POST", "/votes", user_id, {"targetType": target_type, "targetId": target_id})
    except httpx.HTTPStatusError:
        pass  # already voted


def main():
    print("🌱 Seeding test data...\n")

    # --- PINS ---
    pins = [
        {"lat": 40.4168, "lng": -3.7038, "text": "Puerta del Sol"},
        {"lat": 40.4153, "lng": -3.7074, "text": "Plaza Mayor"},
        {"lat": 40.4138, "lng": -3.6921, "text": "Museo del Prado"},
        {"lat": 40.4232, "lng": -3.7123, "text": "Gran Vía"},
        {"lat": 40.4200, "lng": -3.6885, "text": "Retiro Park"},
        {"lat": 40.4189, "lng": -3.7146, "text": "Royal Palace"},
    ]

    created_pins = []
    for pin_data in pins:
        p = api("POST", "/pins", USERS[0], pin_data)
        created_pins.append(p)
        print(f"  📍 Pin created: {p['text']} (id={p['id']})")

    # Vote on pins — give some many votes, some few
    vote_counts = [8, 6, 3, 10, 5, 2]  # votes for each pin
    for i, pin in enumerate(created_pins):
        for j in range(vote_counts[i]):
            vote(USERS[j], "pin", pin["id"])
        print(f"  👍 {pin['text']}: {vote_counts[i]} votes {'✨ (permanent label!)' if vote_counts[i] >= 5 else ''}")

    # --- AREAS ---
    areas = [
        {
            "latlngs": [[40.420, -3.710], [40.420, -3.700], [40.415, -3.700], [40.415, -3.710]],
            "color": "blue", "text": "Hipster Zone", "fontSize": "16px",
        },
        {
            "latlngs": [[40.425, -3.715], [40.425, -3.705], [40.420, -3.705], [40.420, -3.715]],
            "color": "green", "text": "Tourist Area", "fontSize": "18px",
        },
        {
            "latlngs": [[40.412, -3.695], [40.412, -3.685], [40.408, -3.685], [40.408, -3.695]],
            "color": "red", "text": "Party District", "fontSize": "14px",
        },
        {
            "latlngs": [[40.428, -3.700], [40.428, -3.690], [40.424, -3.690], [40.424, -3.700]],
            "color": "blue", "text": "Quiet Neighborhood", "fontSize": "15px",
        },
    ]

    created_areas = []
    for area_data in areas:
        a = api("POST", "/areas", USERS[0], area_data)
        created_areas.append(a)
        print(f"  🗺️  Area created: {a['text']} (id={a['id']})")

    # Vote on areas — "Tourist Area" gets lots of votes (big text), others vary
    area_vote_counts = [4, 9, 7, 1]
    for i, area in enumerate(created_areas):
        for j in range(area_vote_counts[i]):
            vote(USERS[j], "area", area["id"])
        boost = 1 + min(area_vote_counts[i], 50) * 0.02
        print(f"  👍 {area['text']}: {area_vote_counts[i]} votes (font scale: {boost:.0%})")

    print("\n✅ Done! Restart docker or refresh the page to see the test data.")
    print("   Pins with ≥5 votes will show text permanently.")
    print("   Area labels will appear larger based on vote count.")


if __name__ == "__main__":
    main()
