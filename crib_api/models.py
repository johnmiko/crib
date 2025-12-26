
# ===== API Models =====

from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel


class ActionType(str, Enum):
    """Types of actions the game can request from the player."""
    SELECT_CRIB_CARDS = "select_crib_cards"
    SELECT_CARD_TO_PLAY = "select_card_to_play"
    WAITING_FOR_COMPUTER = "waiting_for_computer"
    ROUND_COMPLETE = "round_complete"
    GAME_OVER = "game_over"


class CardData(BaseModel):
    """Representation of a playing card for API responses."""
    rank: str
    suit: str
    symbol: str
    value: int


class PlayerAction(BaseModel):
    """Player's action submission."""
    card_indices: List[int]  # Indices of cards from hand: 2 for crib, 1 for play, 0 for "go"


class GameStateResponse(BaseModel):
    """Complete game state returned to frontend."""
    game_id: str
    action_required: ActionType
    message: str
    your_hand: List[CardData]
    computer_hand: List[CardData]  # For debugging
    table_cards: List[CardData]
    scores: Dict[str, int]  # {"you": 0, "computer": 0}
    dealer: str
    table_value: int
    starter_card: Optional[CardData] = None
    valid_card_indices: List[int]  # Which cards from hand can be played
    game_over: bool = False
    winner: Optional[str] = None
    computer_hand_count: Optional[int] = None
    round_summary: Optional[Dict] = None