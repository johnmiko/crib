"""Test script to verify AI opponents are working."""
import requests
import json

BASE_URL = "http://localhost:8001"

print("Testing AI Opponents Integration")
print("=" * 50)

# Test 1: Get available opponents
print("\n1. Getting available opponents...")
try:
    response = requests.get(f"{BASE_URL}/opponents")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {len(data['opponents'])} opponents:")
        for opp in data['opponents']:
            print(f"  - {opp['name']} (id: {opp['id']})")
    else:
        print(f"✗ Error: {response.status_code}")
except Exception as e:
    print(f"✗ Exception: {e}")

# Test 2: Create games with each AI opponent
print("\n2. Creating games with AI opponents...")
ai_opponents = ['linearb', 'nonlinearb', 'deeppeg', 'myrmidon']

for opponent_id in ai_opponents:
    print(f"\n  Testing {opponent_id}...")
    try:
        response = requests.post(
            f"{BASE_URL}/game/new",
            json={"opponent_type": opponent_id}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"    ✓ Game created successfully (id: {data['game_id'][:8]}...)")
            print(f"    ✓ Message: {data['message']}")
            # Clean up
            requests.delete(f"{BASE_URL}/game/{data['game_id']}")
        else:
            print(f"    ✗ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"    ✗ Exception: {e}")

print("\n" + "=" * 50)
print("Testing complete!")
