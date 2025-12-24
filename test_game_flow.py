"""Test AI opponent integration with actual game flow."""
import sys
sys.path.insert(0, 'C:\\Users\\johnm\\ccode\\crib_back')

from app import GameSession

print("Creating game with LinearB opponent...")
try:
    session = GameSession("test-game", opponent_type="linearb")
    print("✓ Game created successfully")
    
    print("\nStarting round...")
    state = session.get_state()
    print(f"✓ Initial state: {state['message']}")
    print(f"  Action required: {state['action_required']}")
    print(f"  Human hand: {len(state['human_hand'])} cards")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
