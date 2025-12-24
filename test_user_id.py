"""
Simple test to verify user ID generation and match recording works.
Run this after starting the backend to verify the flow.
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_user_flow():
    """Test that a game can be created with a user_id and stats are recorded."""
    
    # Simulate a user ID (in real app, this comes from localStorage)
    user_id = "test-user-12345"
    
    print(f"Testing with user_id: {user_id}")
    
    # Create a game with user_id
    print("\n1. Creating a new game...")
    response = requests.post(
        f"{BASE_URL}/game/new",
        json={
            "opponent_type": "random",
            "user_id": user_id
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create game: {response.status_code}")
        print(response.text)
        return
    
    game_data = response.json()
    game_id = game_data["game_id"]
    print(f"✅ Game created: {game_id}")
    print(f"   Scores: {game_data['scores']}")
    
    # Get user stats (should be empty or show previous games)
    print(f"\n2. Checking user stats before game completion...")
    response = requests.get(f"{BASE_URL}/stats/{user_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get stats: {response.status_code}")
        return
    
    stats_before = response.json()
    print(f"✅ Stats retrieved:")
    print(json.dumps(stats_before, indent=2))
    
    print("\n✅ User ID flow is working!")
    print(f"\nTo test match recording:")
    print(f"1. Play a complete game using the frontend")
    print(f"2. Check your browser's localStorage for 'crib-user-id'")
    print(f"3. Call GET /stats/<your-user-id> to see recorded matches")
    print(f"\nExample: curl {BASE_URL}/stats/<your-user-id>")

if __name__ == "__main__":
    try:
        # Check if backend is running
        response = requests.get(f"{BASE_URL}/healthcheck")
        if response.status_code != 200:
            print("❌ Backend is not responding correctly")
            exit(1)
        
        test_user_flow()
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to backend at {BASE_URL}")
        print("Make sure the backend is running: uvicorn app:app --reload --host 0.0.0.0 --port 8001")
    except Exception as e:
        print(f"❌ Error: {e}")
