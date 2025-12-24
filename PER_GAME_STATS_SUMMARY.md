# Per-Game Stats Implementation - Summary

## ✅ What's Been Implemented

### 1. New Database Schema
- Renamed `match_history` table to `game_results`
- Changed from aggregated wins/losses to per-game tracking
- Each game is now a separate record with detailed stats

### 2. New Tracked Statistics
Three new metrics per game:

**average_points_pegged**
- Points you earned during pegging phases
- Average across all pegging rounds in that game
- Shows pegging strategy effectiveness

**average_hand_score**
- Points from hands you played
- Average per hand participated
- Reflects card selection quality

**average_crib_score**
- Points from crib (when you were dealer)
- Average when you dealt the crib
- Tracks crib card selection skill

### 3. Database Structure
```
game_results table:
- id (primary key)
- user_id (index)
- opponent_id (index)
- win (boolean: 1 for win, 0 for loss)
- average_points_pegged (float)
- average_hand_score (float)
- average_crib_score (float)
- created_at (timestamp)
```

### 4. New API Endpoints

**GET /stats/{user_id}** - Aggregated stats
- Returns wins/losses/totals by opponent
- Includes new average metrics per opponent

**GET /stats/{user_id}/history** - Individual games
- Returns list of all games in chronological order
- Each game includes all metrics
- Supports filtering by opponent_id and limiting results
- Perfect for creating charts/graphs

### 5. Stat Tracking During Gameplay

**GameSession** now tracks:
- `total_points_pegged_human` - Sum of all pegging points
- `total_hand_score_human` - Sum of all hand scores
- `total_crib_score_human` - Sum of crib scores when dealer
- Counts for normalization (hands, pegging rounds, dealer times)

**ResumableRound** now tracks:
- `pegging_scores` - Points awarded in each pegging action
- `pegging_rounds_count` - Number of scoring actions

**When game ends:**
- Calculates averages: total / count
- Calls `record_match_result()` with all stats
- Creates a single game_results row

## 📊 Data You Can Now Visualize

### Line Charts Over Time
```
Game 1: avg_points_pegged=5,  avg_hand_score=8,   avg_crib_score=6
Game 2: avg_points_pegged=7,  avg_hand_score=10,  avg_crib_score=5
Game 3: avg_points_pegged=9,  avg_hand_score=12,  avg_crib_score=8
Game 4: avg_points_pegged=8,  avg_hand_score=11,  avg_crib_score=7
...

Trend: Points pegged improving, hand scores improving, crib scores stable
```

### Aggregated Performance
```
Opponent: "random" (15 games)
- Wins: 10, Losses: 5, Win rate: 66.7%
- Avg points pegged: 7.2
- Avg hand score: 10.5
- Avg crib score: 6.8
```

## 🔄 Migration Required

### For Existing Users
The old `match_history` table is replaced with `game_results`. 

**Steps:**
1. Backup old data (optional):
   ```bash
   # Export from old table if needed
   ```
2. Restart backend - new table auto-creates
3. Play new games - stats accumulate in new table

**Old data:** Will remain in old table but won't be used. Can be deleted safely.

## 💻 Files Changed

**Backend (crib_back):**
- ✏️ `database.py` - New GameResult model, updated functions
- ✏️ `app.py` - GameSession stat tracking, new endpoints
- ✨ `DATABASE_MIGRATION.md` - Migration guide
- ✨ `test_advanced_stats.py` - Test script

## 🧪 Testing

### Quick Test
```powershell
cd c:\Users\johnm\ccode\crib_back
activate
python test_advanced_stats.py
```

This verifies:
- Database connectivity
- Stats endpoints work
- New metrics are tracked

### Manual Test
1. Start backend: `uvicorn app:app --reload --host 0.0.0.0 --port 8001`
2. Play a complete game to 121 points
3. Check stats:
   ```bash
   # Aggregated
   curl http://localhost:8001/stats/<your-user-id>
   
   # Individual games
   curl http://localhost:8001/stats/<your-user-id>/history
   ```

## 🚀 Next Steps (From Your To-Do)

Now that per-game tracking is in place:

1. **Create Frontend Stats Page**
   - Display win/loss records
   - Show charts using recharts or similar
   - Display trending metrics

2. **Build Charts**
   - Line chart: avg_points_pegged over 10 last games
   - Line chart: avg_hand_score over time
   - Line chart: win rate (rolling average)
   - Bar chart: performance by opponent

3. **Add More Features**
   - Best game stats (highest points_pegged)
   - Streak tracking (current wins/losses)
   - Comparison vs opponents
   - Export as CSV

## 📝 API Examples

### Get Aggregated Stats
```bash
curl http://localhost:8001/stats/user-123

Response:
{
  "user_id": "user-123",
  "stats": [
    {
      "opponent_id": "random",
      "wins": 10,
      "losses": 5,
      "total_games": 15,
      "win_rate": 0.667,
      "avg_points_pegged": 7.2,
      "avg_hand_score": 10.5,
      "avg_crib_score": 6.8
    }
  ]
}
```

### Get Individual Games
```bash
curl "http://localhost:8001/stats/user-123/history?opponent_id=random&limit=10"

Response:
{
  "user_id": "user-123",
  "opponent_id": "random",
  "games": [
    {
      "id": 42,
      "opponent_id": "random",
      "win": true,
      "average_points_pegged": 8.5,
      "average_hand_score": 12.3,
      "average_crib_score": 7.8,
      "created_at": "2025-12-24T15:30:00"
    },
    ...
  ]
}
```

## ✨ Why This Design

1. **Per-game data** - Can track improvement over time (vs aggregated)
2. **Single "win" field** - Cleaner than separate wins/losses columns
3. **Averages not totals** - Fair comparison regardless of game length
4. **Three metrics** - Cover pegging, hand play, and crib skills
5. **Two endpoints** - One for summary, one for detailed analysis

This structure gives you everything needed to create meaningful analytics and charts showing your skill development! 🎮📈
