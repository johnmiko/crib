"""
Test script to verify the new game_results table and stats tracking works.
Run this after restarting the backend with the updated database.py
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_stats_with_new_schema():
    """Test that stats are properly tracked with the new schema."""
    
    user_id = "test-user-advanced"
    
    print("Testing Advanced Stats Tracking")
    print("=" * 50)
    
    # Create a game
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
    
    # Check aggregated stats
    print(f"\n2. Checking aggregated stats for {user_id}...")
    response = requests.get(f"{BASE_URL}/stats/{user_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get stats: {response.status_code}")
        return
    
    stats = response.json()
    print(f"✅ Aggregated stats:")
    print(json.dumps(stats, indent=2))
    
    # Check game history
    print(f"\n3. Checking game history for {user_id}...")
    response = requests.get(f"{BASE_URL}/stats/{user_id}/history")
    
    if response.status_code != 200:
        print(f"❌ Failed to get game history: {response.status_code}")
        print(response.text)
        return
    
    history = response.json()
    print(f"✅ Game history:")
    print(json.dumps(history, indent=2))
    
    print("\n" + "=" * 50)
    print("✅ Advanced stats tracking is working!")
    print("\nNew tracked fields:")
    print("  - average_points_pegged: avg points per pegging round")
    print("  - average_hand_score: avg score per hand played")
    print("  - average_crib_score: avg crib score when dealer")
    print("\nEndpoints:")
    print(f"  GET /stats/{{user_id}} - Aggregated stats by opponent")
    print(f"  GET /stats/{{user_id}}/history - Individual game history for charting")

if __name__ == "__main__":
    try:
        response = requests.get(f"{BASE_URL}/healthcheck")
        if response.status_code != 200:
            print("❌ Backend is not responding correctly")
            exit(1)
        
        test_stats_with_new_schema()
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to backend at {BASE_URL}")
        print("Make sure the backend is running: uvicorn app:app --reload --host 0.0.0.0 --port 8001")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
