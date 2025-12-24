"""Test database match statistics functionality."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, record_match_result, get_user_stats

# Mock DATABASE_URL for testing (you can skip this if Railway is already configured)
# os.environ['DATABASE_URL'] = 'postgresql://user:password@localhost:5432/cribbage'

print("Testing Database Integration")
print("=" * 60)

# Test 1: Initialize database
print("\n1. Initializing database...")
try:
    init_db()
    print("   ✓ Database initialized (or DATABASE_URL not set)")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: Record match result without user_id (should skip)
print("\n2. Testing record_match_result with user_id=None...")
try:
    result = record_match_result(None, "linearb", True)
    if not result:
        print("   ✓ Correctly skipped recording (no user_id)")
    else:
        print("   ✗ Should have returned False for None user_id")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: Record match result with user_id (will only work if DATABASE_URL is set)
print("\n3. Testing record_match_result with user_id='test_user'...")
try:
    result = record_match_result("test_user", "linearb", True)
    if result:
        print("   ✓ Match result recorded successfully")
    else:
        print("   ⚠ Recording skipped (DATABASE_URL not set)")
except Exception as e:
    print(f"   ⚠ Error (expected if no database): {e}")

# Test 4: Get user stats
print("\n4. Testing get_user_stats for 'test_user'...")
try:
    stats = get_user_stats("test_user")
    if stats:
        print(f"   ✓ Stats retrieved: {stats}")
    else:
        print("   ⚠ No stats found (DATABASE_URL not set or no matches)")
except Exception as e:
    print(f"   ⚠ Error (expected if no database): {e}")

print("\n" + "=" * 60)
print("Database test complete!")
print("\nNotes:")
print("- If DATABASE_URL is not set, database operations gracefully skip")
print("- When user_id is None, recording is skipped (anonymous users)")
print("- Set DATABASE_URL environment variable from Railway to enable tracking")
