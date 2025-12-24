# localStorage UUID User Tracking - Quick Start

## ✅ What's Implemented

1. **Frontend Auto-Generated User IDs**
   - Browser localStorage stores a persistent UUID
   - Automatically sent with every game creation
   - No login required

2. **Backend Match Recording**
   - Stores wins/losses per opponent type
   - Auto-saves when games end (≥121 points)
   - Optional database (works without it too)

3. **Stats API**
   - `GET /stats/{user_id}` returns match history
   - Shows wins, losses, win rate by opponent

## 🚀 Try It Now

### See Your User ID
1. Open crib_front in browser
2. Open browser console (F12)
3. Type: `localStorage.getItem('crib-user-id')`

### Play and Track
1. Play a complete game to 121 points
2. Your match is automatically recorded (if database is connected)
3. Check stats: `http://localhost:8001/stats/<your-user-id>`

### Test Without Playing
```powershell
cd c:\Users\johnm\ccode\crib_back
activate
python test_user_id.py
```

## 📁 Files Created/Modified

**crib_front:**
- ✨ Created: [src/lib/userId.ts](c:\Users\johnm\ccode\crib_front\src\lib\userId.ts)
- ✏️ Modified: [src/lib/api.ts](c:\Users\johnm\ccode\crib_front\src\lib\api.ts)

**crib_back:**
- ✨ Created: [test_user_id.py](c:\Users\johnm\ccode\crib_back\test_user_id.py)
- ✨ Created: [.env.example](c:\Users\johnm\ccode\crib_back\.env.example)
- ✨ Created: [USER_ID_IMPLEMENTATION.md](c:\Users\johnm\ccode\crib_back\USER_ID_IMPLEMENTATION.md)

## 🎯 Next Steps (From Your To-Do List)

Now that user tracking works, you can:

1. **Add More Match Data**
   - points_pegged (average per hand)
   - average_hand_score
   - average_crib_score

2. **Create Match History UI**
   - Show recent games
   - Display win/loss charts
   - Track progress over time

3. **Deploy to Railway**
   - Database will auto-configure
   - Match history persists across devices

4. **Upgrade to Google SSO Later**
   - Migrate anonymous IDs to real accounts
   - Sync across devices
   - Preserve existing stats

## 🔍 How It Works

```
Browser                Frontend              Backend              Database
  │                       │                     │                     │
  │ localStorage         │                     │                     │
  │ generates UUID       │                     │                     │
  │                      │                     │                     │
  │ ──────────────────>  │                     │                     │
  │   getUserId()        │                     │                     │
  │ <──────────────────  │                     │                     │
  │   "abc-123-def"      │                     │                     │
  │                      │                     │                     │
  │ Start Game           │                     │                     │
  │ ──────────────────>  │ POST /game/new      │                     │
  │                      │ {user_id: "abc-.."}│                     │
  │                      │ ──────────────────> │                     │
  │                      │                     │                     │
  ... play game to 121 points ...              │                     │
  │                      │                     │                     │
  │                      │                     │ INSERT wins/losses  │
  │                      │                     │ ──────────────────> │
  │                      │                     │                     │
  │ Check Stats          │ GET /stats/abc-..   │                     │
  │ ──────────────────>  │ ──────────────────> │ SELECT * FROM...   │
  │                      │                     │ ──────────────────> │
  │                      │                     │ <────────────────── │
  │ <──────────────────  │ <──────────────────  │                     │
  │ {wins: 5, losses: 3} │                     │                     │
```

## 💡 Key Features

- ✅ Zero configuration for users
- ✅ Persists across browser sessions
- ✅ Works without database (degrades gracefully)
- ✅ Ready for Google SSO upgrade later
- ✅ Anonymous and privacy-friendly

## 📝 API Example

```bash
# Get your user ID from browser console first
curl http://localhost:8001/stats/550e8400-e29b-41d4-a716-446655440000

# Response:
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "stats": [
    {
      "opponent_id": "linearb",
      "wins": 12,
      "losses": 8,
      "total_games": 20,
      "win_rate": 0.6
    }
  ]
}
```

---

✨ **Ready to use!** Start the frontend and backend, and your matches will be tracked automatically.
