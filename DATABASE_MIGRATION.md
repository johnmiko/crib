# Database Migration: Per-Game Stats Tracking

## Overview
Changed from aggregated wins/losses tracking to per-game detailed stats. This allows tracking performance metrics over time and creating charts to visualize improvement.

## What Changed

### Old Schema (match_history table)
```
- user_id
- opponent_id
- wins (accumulated)
- losses (accumulated)
- created_at
- updated_at
```

### New Schema (game_results table)
```
- id (primary key)
- user_id
- opponent_id
- win (boolean) - True/False instead of separate wins/losses
- average_points_pegged (float)
- average_hand_score (float)
- average_crib_score (float)
- created_at
```

## New Tracked Metrics

### average_points_pegged
- Average points earned during pegging phases
- Calculated across all pegging rounds in a game
- Useful for tracking pegging strategy improvement

### average_hand_score
- Average score from hand cards played
- Calculated per hand the player participated in
- Tracks how well you're selecting cards

### average_crib_score
- Average score from the crib (when you were dealer)
- Calculated only for hands where you were the crib dealer
- Tracks crib card selection quality

## Migration Steps

### Local Development

#### If using Railway database:
1. Connect to the old database and export data (optional):
   ```bash
   # Your old data can be backed up if needed
   ```

2. The new `game_results` table will be created automatically on app restart

3. Old `match_history` table will remain but won't be used

#### If using local SQLite/no database:
- No action needed, just restart the backend
- Tables are created automatically

### After Migration

1. Restart the backend:
   ```powershell
   cd c:\Users\johnm\ccode\crib_back
   activate
   
   # Backend will auto-create new table on startup
   uvicorn app:app --reload --host 0.0.0.0 --port 8001
   ```

2. Play a complete game to 121 points

3. Check stats:
   ```bash
   # Get aggregated stats
   curl http://localhost:8001/stats/<your-user-id>
   
   # Get individual game history (for charting)
   curl http://localhost:8001/stats/<your-user-id>/history
   ```

4. Test with included script:
   ```powershell
   python test_advanced_stats.py
   ```

## API Changes

### GET /stats/{user_id} - Aggregated Stats
**Before:**
```json
{
  "user_id": "...",
  "stats": [
    {
      "opponent_id": "random",
      "wins": 5,
      "losses": 3,
      "total_games": 8,
      "win_rate": 0.625
    }
  ]
}
```

**After:**
```json
{
  "user_id": "...",
  "stats": [
    {
      "opponent_id": "random",
      "wins": 5,
      "losses": 3,
      "total_games": 8,
      "win_rate": 0.625,
      "avg_points_pegged": 8.5,
      "avg_hand_score": 12.3,
      "avg_crib_score": 7.8
    }
  ]
}
```

### GET /stats/{user_id}/history - NEW!
Returns individual game records for charting:
```json
{
  "user_id": "...",
  "opponent_id": null,
  "games": [
    {
      "id": 1,
      "opponent_id": "random",
      "win": true,
      "average_points_pegged": 8.5,
      "average_hand_score": 12.3,
      "average_crib_score": 7.8,
      "created_at": "2025-12-24T10:30:00"
    },
    ...
  ]
}
```

## Rollback (if needed)

If you need to revert to the old schema:

1. Edit `database.py` and restore the old `MatchHistory` class
2. Run:
   ```python
   from database import init_db
   init_db()  # This will create the old table
   ```

Note: You'll lose the new game results data.

## Future Enhancements

With per-game data, you can now:

1. **Create Charts**
   - Line graph: average_points_pegged over time
   - Line graph: average_hand_score over time
   - Line graph: win rate over last N games

2. **Track Streaks**
   - Current win/loss streak
   - Best/worst performance periods

3. **Compare Opponents**
   - Performance vs each AI opponent
   - Win rate trends per opponent

4. **Export Data**
   - CSV export of game history
   - JSON export for analysis

## Code Changes

### database.py
- Replaced `MatchHistory` table with `GameResult` table
- Updated `record_match_result()` to accept new stats parameters
- Updated `get_user_stats()` to aggregate per-game data
- Added `get_game_history()` for retrieving individual games

### app.py
- Added stat tracking fields to `GameSession`
- Added `calculate_game_stats()` method to compute averages
- Modified `advance()` to track hand scores and crib scores
- Modified `ResumableRound` to track pegging scores
- Added `/stats/{user_id}/history` endpoint
- Updated game-over logic to pass stats to `record_match_result()`

## Testing

Run the test script to verify everything works:
```powershell
python test_advanced_stats.py
```

This will:
1. Create a new game with user_id
2. Fetch aggregated stats
3. Fetch individual game history
4. Display both responses
