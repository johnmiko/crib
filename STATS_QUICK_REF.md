# Per-Game Stats - Quick Reference

## Changes Made

### Database
| Old | New |
|-----|-----|
| `match_history` table | `game_results` table |
| Aggregated wins/losses | Individual game records |
| Updated/created_at | Only created_at |

### New Columns
```
win (boolean)              - 1 if won, 0 if lost
average_points_pegged      - Avg pegging points per round
average_hand_score         - Avg hand score per hand played
average_crib_score         - Avg crib score when dealer
```

### API Endpoints
```
GET /stats/{user_id}              - Aggregated (wins/losses + averages)
GET /stats/{user_id}/history      - Individual games for charting
  ?opponent_id={opponent}         - Filter by opponent
  ?limit={N}                      - Return N most recent (default 50)
```

## Setup

### 1. Verify Backend Has Changes
Backend should have:
- New `GameResult` model in `database.py`
- Stats tracking in `GameSession` (app.py)
- New `/stats/{user_id}/history` endpoint

### 2. Restart Backend
```powershell
cd c:\Users\johnm\ccode\crib_back
activate
uvicorn app:app --reload --host 0.0.0.0 --port 8001
```

### 3. Old Table Persists
- Old `match_history` table remains but unused
- Can safely delete after verifying new data

## Test It

### Option 1: Run Test Script
```powershell
python test_advanced_stats.py
```

### Option 2: Manual Steps
1. Play a complete game
2. Check browser console: `window.cribDebug.getStats()`
3. Query API manually:
   ```bash
   curl http://localhost:8001/stats/<your-user-id>/history
   ```

## Example Response

### /stats/{user_id}
```json
{
  "user_id": "abc-123",
  "stats": [
    {
      "opponent_id": "random",
      "wins": 5,
      "losses": 3,
      "total_games": 8,
      "win_rate": 0.625,
      "avg_points_pegged": 7.2,
      "avg_hand_score": 10.5,
      "avg_crib_score": 6.8
    }
  ]
}
```

### /stats/{user_id}/history
```json
{
  "user_id": "abc-123",
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
    }
  ]
}
```

## Metrics Explained

| Metric | Meaning |
|--------|---------|
| `average_points_pegged` | Avg pts during pegging phases (shows pegging skill) |
| `average_hand_score` | Avg pts from hand cards (shows hand card selection) |
| `average_crib_score` | Avg pts from crib when dealer (shows crib skill) |

## Frontend Integration (Next)

Once confirmed working:

1. Create stats component
2. Fetch from `/stats/{user_id}/history`
3. Create charts with recharts:
   - Line: avg_points_pegged over games
   - Line: avg_hand_score over games  
   - Line: win_rate (rolling)
4. Show aggregated stats from `/stats/{user_id}`

## Deployment

No special steps needed:
- Railway auto-creates tables on deploy
- Uses `DATABASE_URL` env var automatically
- Old data safe if present

## Troubleshooting

**"Cannot find column..."**
- Backend wasn't restarted after code changes
- Solution: Stop and restart uvicorn

**"Game history returns empty"**
- New games recorded but must play to 121 points
- Check aggregated stats first: `/stats/{user_id}`

**"404 on /stats/{user_id}/history"**
- Backend code not updated
- Verify app.py has new endpoint
- Check that you imported `get_game_history` from database.py
