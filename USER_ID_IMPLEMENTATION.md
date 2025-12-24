# User ID and Match History Implementation

## Overview
localStorage UUID-based user tracking is now implemented. Users get a persistent anonymous ID that tracks their match statistics across sessions.

## How It Works

### Frontend (crib_front)
1. **User ID Generation**: On first visit, [`userId.ts`](c:\Users\johnm\ccode\crib_front\src\lib\userId.ts) generates a UUID and stores it in localStorage under key `crib-user-id`
2. **API Integration**: [`api.ts`](c:\Users\johnm\ccode\crib_front\src\lib\api.ts) automatically includes the user_id when creating new games
3. **Persistence**: The ID persists across browser sessions (unless user clears localStorage)

### Backend (crib_back)
1. **Database Table**: `match_history` table stores user_id, opponent_id, wins, losses
2. **Auto-Recording**: When a game ends (score ≥ 121), the result is automatically saved to the database
3. **Stats API**: `GET /stats/{user_id}` returns win/loss statistics by opponent type

## Files Changed

### Frontend
- **Created**: [`src/lib/userId.ts`](c:\Users\johnm\ccode\crib_front\src\lib\userId.ts) - UUID generation and localStorage management
- **Modified**: [`src/lib/api.ts`](c:\Users\johnm\ccode\crib_front\src\lib\api.ts) - Added user_id to game creation

### Backend  
- **Existing**: [`database.py`](c:\Users\johnm\ccode\crib_back\database.py) - Already had MatchHistory table and recording logic
- **Existing**: [`app.py`](c:\Users\johnm\ccode\crib_back\app.py) - Already calls `record_match_result()` on game completion

## Database Setup

### Local Development (Optional)
If you want to test database features locally:

1. Install PostgreSQL locally
2. Create a database: `createdb crib`
3. Create `.env` file in crib_back:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/crib
   ```
4. Start the backend - tables will be created automatically

### Without Database
- The app works fine without a database
- Match recording is silently skipped if DATABASE_URL is not set
- Users can still play games normally

### Railway Deployment
- Create a PostgreSQL database on Railway
- Railway automatically injects `DATABASE_URL` into your backend
- Tables are created automatically on first deployment

## Testing

### Quick Test (No Database Required)
```powershell
# In crib_front, check localStorage in browser console
localStorage.getItem('crib-user-id')  # Should show your UUID
```

### With Database
```powershell
# In crib_back directory
cd c:\Users\johnm\ccode\crib_back
activate
python test_user_id.py
```

This will:
1. Create a game with a test user_id
2. Verify the stats endpoint works
3. Show you how to check stats after playing

### Full End-to-End Test
1. Start backend: `uvicorn app:app --reload --host 0.0.0.0 --port 8001`
2. Start frontend: `npm run dev`
3. Play a complete game (to 121 points)
4. Check browser console: `localStorage.getItem('crib-user-id')`
5. Call stats API: `curl http://localhost:8001/stats/<your-user-id>`

## API Endpoints

### Create Game with User ID
```
POST /game/new
{
  "opponent_type": "random",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Get User Stats
```
GET /stats/550e8400-e29b-41d4-a716-446655440000

Response:
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
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

## Utility Functions

### Get User ID
```typescript
import { getUserId } from './lib/userId';
const userId = getUserId();  // Returns existing or generates new
```

### Clear User ID (for testing)
```typescript
import { clearUserId } from './lib/userId';
clearUserId();  // Removes from localStorage
```

## Next Steps

Once this is working, you can:
1. **Add UI for stats**: Display win/loss records in the frontend
2. **Upgrade to Google SSO**: Migrate anonymous users to real accounts
3. **Add more stats**: Track average points, pegging performance, etc.
4. **Leaderboards**: Compare users (with opt-in)

## Notes
- User IDs are anonymous and stored only in browser
- No personal information is collected
- Users can reset by clearing localStorage
- Database is optional for basic gameplay
