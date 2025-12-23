"""FastAPI backend for Cribbage game using existing cribbagegame classes."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional, List, Literal
import uuid

from cribbage.cribbagegame import CribbageGame, CribbageRound, debug
from cribbage.player import Player, RandomPlayer
from cribbage.models import ActionType, GameStateResponse, PlayerAction, CardData
from cribbage.playingcards import Card, Deck
from pydantic import BaseModel


app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AwaitingPlayerInput(Exception):
    """Raised when the game needs input from the human player."""
    def __init__(self, msg: str, cards: List[Card], n_cards: int):
        self.msg = msg
        self.cards = cards
        self.n_cards = n_cards
        super().__init__(msg)


class APIPlayer(Player):
    """Player that pauses game execution when input is needed."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.pending_selection: Optional[str] = None
    
    def set_selection(self, selection: str):
        """Set the selection from the API."""
        self.pending_selection = selection
    
    def get_input(self, msg: str, cards: List[Card], n_cards: int) -> str:
        """Get input - either from pending selection or raise exception to pause."""
        if self.pending_selection is not None:
            selection = self.pending_selection
            self.pending_selection = None
            return selection
        raise AwaitingPlayerInput(msg, cards, n_cards)
    
    def select_crib_cards(self, hand):
        """Select cards for the crib."""
        cards_selected = []
        while len(cards_selected) < 2:
            selection = self.get_input("Select 2 cards: ", hand, 2)
            indices = [int(s) for s in selection.split() if s.isdigit()]
            for idx in indices:
                if idx < 1 or idx > len(hand):
                    continue
                cards_selected.append(hand[idx - 1])
        return cards_selected
    
    def select_card_to_play(self, hand, table, crib):
        """Select a card to play."""
        if not hand:
            return None
        selection = self.get_input("Select a card: ", hand, 1)
        if not selection.strip():
            return None
        indices = [int(s) for s in selection.split() if s.isdigit()]
        if indices:
            idx = indices[0]
            if 1 <= idx <= len(hand):
                return hand[idx - 1]
        return None


def card_to_data(card: Card) -> CardData:
    """Convert a Card object to CardData."""
    return CardData(
        rank=card.get_rank(),
        suit=card.get_suit(),
        value=card.get_value(),
        symbol=str(card)
    )


class ResumableRound:
    """Wrapper around CribbageRound that can be paused and resumed."""
    
    def __init__(self, game, dealer):
        self.round = CribbageRound(game=game, dealer=dealer)
        self.phase = 'start'
        self.active_players = None
        self.sequence_start_idx = 0
        # Optional overrides for deterministic starts
        self.overrides: Dict = {}
        
    def run(self):
        """Run the round until completion or until player input needed."""
        r = self.round
        
        if self.phase == 'start':
            r._cut()
            r._deal()
            # Apply any deal/hand overrides for deterministic test sessions
            if self.overrides.get('hands'):
                # Build a set of (rank_name, suit_name) for removal from deck
                def _key(c: Card):
                    return (c.get_rank(), c.get_suit())
                remove_keys = set()
                for plist in self.overrides['hands'].values():
                    for c in plist:
                        remove_keys.add(_key(c))
                # Filter deck to remove overridden cards so no duplicates appear later
                r.deck.cards = [c for c in r.deck.cards if _key(c) not in remove_keys]
                # Overwrite hands
                r.hands = {p: list(self.overrides['hands'].get(p, r.hands[p])) for p in r.hands}
            self.phase = 'crib'
        
        if self.phase == 'crib':
            r._populate_crib()  # May raise AwaitingPlayerInput
            r._cut()
            r.starter = r.deck.draw()
            if r.starter.get_rank() == 'jack':
                r.game.board.peg(r.dealer, 1)
            self.active_players = [r.nondealer, r.dealer]
            self.phase = 'play'
        
        if self.phase == 'play':
            # If we're resuming with a pending human selection, ensure human acts first
            try:
                from app import APIPlayer as _APIPlayer  # local check without circular import issues
            except Exception:
                _APIPlayer = APIPlayer  # fallback when already in this module
            if self.active_players:
                # Prioritize APIPlayer with a pending selection so we don't let the computer sneak an extra turn
                def _priority(p):
                    if isinstance(p, _APIPlayer) and getattr(p, 'pending_selection', None) is not None:
                        return 0
                    return 1
                # Stable sort keeps other order but moves the human with pending selection to front
                self.active_players = sorted(self.active_players, key=_priority)

            while sum([len(v) for v in r.hands.values()]):
                while self.active_players:
                    players_to_check = list(self.active_players)
                    for p in players_to_check:
                        # Debug current selection context
                        try:
                            seq_cards = ", ".join(str(m['card']) for m in r.table[self.sequence_start_idx:])
                        except Exception:
                            seq_cards = ""
                        debug(f"[PLAY] Next: {p} | seq=[{seq_cards}] | value={r.get_table_value(self.sequence_start_idx)} | hand={r.hands.get(p, [])}")
                        card = p.select_card_to_play(
                            hand=r.hands[p],
                            table=r.table[self.sequence_start_idx:],
                            crib=r.crib
                        )  # May raise AwaitingPlayerInput
                        
                        if card is None or card.get_value() + r.get_table_value(self.sequence_start_idx) > 31:
                            debug(f"[GO] {p} cannot play or chose go (value={r.get_table_value(self.sequence_start_idx)})")
                            self.active_players.remove(p)
                        else:
                            r.table.append({'player': p, 'card': card})
                            r.hands[p].remove(card)
                            if not r.hands[p]:
                                self.active_players.remove(p)
                            debug(f"[PLAY] {p} plays {card} -> value={r.get_table_value(self.sequence_start_idx)}")
                            score = r._score_play(card_seq=[move['card'] for move in r.table[self.sequence_start_idx:]])
                            if score:
                                r.game.board.peg(p, score)
                
                r.go_or_31_reached(self.active_players)
                # Reset sequence start for next sequence after go/31
                self.sequence_start_idx = len(r.table)
                self.active_players = [p for p in r.game.players if r.hands[p]]
            
            self.phase = 'scoring'
        
        if self.phase == 'scoring':
            for p in r.game.players:
                p_cards_played = [move['card'] for move in r.table if move['player'] == p]
                score = r._score_hand(cards=p_cards_played + [r.starter])
                if score:
                    r.game.board.peg(p, score)
            
            score = r._score_hand(cards=(r.crib + [r.starter]))
            if score:
                r.game.board.peg(r.dealer, score)
            
            self.phase = 'complete'
    
    @property
    def hands(self):
        return self.round.hands
    
    @property
    def table(self):
        return self.round.table
    
    @property
    def starter(self):
        return self.round.starter
    
    @property
    def dealer(self):
        return self.round.dealer


class GameSession:
    """Manages a single game session with pause/resume capability."""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.human = APIPlayer("human")
        self.computer = RandomPlayer("computer")
        self.game = CribbageGame(players=[self.human, self.computer])
        self.current_round: Optional[ResumableRound] = None
        self.waiting_for: Optional[ActionType] = None
        self.message: str = ""
        self.last_cards: List[Card] = []
        self.last_n_cards: int = 0
        self.game_over: bool = False
        self.round_num: int = 0
        # One-time overrides for next new round
        self.next_dealer_override: Optional[Player] = None
        self.next_round_overrides: Dict = {}
        
    def get_state(self) -> GameStateResponse:
        """Get current game state."""
        your_hand = []
        computer_hand = []
        table_cards = []
        table_value = 0
        starter_card = None
        valid_indices = []
        
        if self.current_round:
            your_hand = [card_to_data(c) for c in self.current_round.hands.get(self.human, [])]
            computer_hand = [card_to_data(c) for c in self.current_round.hands.get(self.computer, [])]
            table_cards = [card_to_data(m['card']) for m in self.current_round.table]
            
            if self.current_round.table:
                # Use the active sequence_start_idx tracked by the resumable round
                sequence_start = getattr(self.current_round, 'sequence_start_idx', None)
                if sequence_start is None:
                    # Fallback: if we can't determine the sequence start, 
                    # conservatively show 0 (should rarely happen)
                    sequence_start = len(self.current_round.table)
                table_value = sum(m['card'].get_value() for m in self.current_round.table[sequence_start:])

            
            if self.current_round.starter:
                starter_card = card_to_data(self.current_round.starter)
            
            # Calculate valid card indices
            if self.waiting_for == ActionType.SELECT_CARD_TO_PLAY:
                for i, card in enumerate(self.current_round.hands.get(self.human, [])):
                    if card.get_value() + table_value <= 31:
                        valid_indices.append(i)
            elif self.waiting_for == ActionType.SELECT_CRIB_CARDS:
                valid_indices = list(range(len(your_hand)))
        
        # Check for winner
        winner = None
        for p in self.game.players:
            if self.game.board.get_score(p) >= 121:
                self.game_over = True
                winner = str(p).lower()
                break
        
        # Get dealer
        dealer = "none"
        if self.current_round and self.current_round.dealer:
            dealer = str(self.current_round.dealer).lower()
        
        # Map player names to frontend-expected names
        scores_dict = {}
        for p in self.game.players:
            player_name = str(p).lower()
            # Map "human" to "you" for frontend compatibility
            if player_name == "human":
                scores_dict["you"] = self.game.board.get_score(p)
            else:
                scores_dict[player_name] = self.game.board.get_score(p)
        
        # Also map dealer name if it's "human"
        if dealer == "human":
            dealer = "you"
        
        return GameStateResponse(
            game_id=self.game_id,
            action_required=self.waiting_for or ActionType.WAITING_FOR_COMPUTER,
            message=self.message,
            your_hand=your_hand,
            computer_hand=computer_hand,
            table_cards=table_cards,
            scores=scores_dict,
            dealer=dealer,
            table_value=table_value,
            starter_card=starter_card,
            valid_card_indices=valid_indices,
            game_over=self.game_over,
            winner=winner
        )
    
    def start_new_round(self):
        """Start a new round."""
        if self.next_dealer_override is not None:
            dealer = self.next_dealer_override
            # Clear override after use
            self.next_dealer_override = None
        else:
            dealer = self.game.players[self.round_num % len(self.game.players)]
        self.current_round = ResumableRound(game=self.game, dealer=dealer)
        if self.next_round_overrides:
            self.current_round.overrides = self.next_round_overrides
            self.next_round_overrides = {}
        self.round_num += 1
    
    def advance(self) -> GameStateResponse:
        """Advance the game until player input is needed."""
        try:
            # Start new round if needed
            if self.current_round is None:
                self.start_new_round()
            
            # Run the round (will pause if player input needed)
            self.current_round.run()
            
            # If we reach here without exception, round completed
            # Check if game is over
            for p in self.game.players:
                if self.game.board.get_score(p) >= 121:
                    self.game_over = True
                    self.message = f"Game over! {p} wins!"
                    return self.get_state()
            
            # Start new round
            self.current_round = None
            return self.advance()
            
        except AwaitingPlayerInput as e:
            # Game paused waiting for player input
            self.last_cards = e.cards
            self.last_n_cards = e.n_cards
            self.message = e.msg
            
            if e.n_cards == 2:
                self.waiting_for = ActionType.SELECT_CRIB_CARDS
            elif e.n_cards == 1:
                self.waiting_for = ActionType.SELECT_CARD_TO_PLAY
            
            return self.get_state()

    
    def submit_action(self, card_indices: List[int]) -> GameStateResponse:
        """Submit player action and continue game."""
        if self.waiting_for == ActionType.SELECT_CRIB_CARDS:
            if len(card_indices) != 2:
                raise HTTPException(status_code=400, detail="Must select exactly 2 cards for crib")
            # Convert 0-based indices to 1-based selection string
            selection = " ".join(str(i + 1) for i in sorted(card_indices))
        elif self.waiting_for == ActionType.SELECT_CARD_TO_PLAY:
            if len(card_indices) == 0:
                selection = ""  # Go
            elif len(card_indices) == 1:
                selection = str(card_indices[0] + 1)
            else:
                raise HTTPException(status_code=400, detail="Must select 0 or 1 card to play")
        else:
            raise HTTPException(status_code=400, detail="No action required")
        
        # Validate indices
        for idx in card_indices:
            if idx < 0 or idx >= len(self.last_cards):
                raise HTTPException(status_code=400, detail=f"Invalid card index: {idx}")
        
        # Set the selection and continue
        self.human.set_selection(selection)
        self.waiting_for = None
        return self.advance()


# Request model for creating a new game with optional overrides
class CreateGameRequest(BaseModel):
    dealer: Optional[Literal['human','computer','you','player']] = None
    preset: Optional[Literal['aces_twos_vs_threes_fours']] = None
    # Future: explicit card lists like ["ace-hearts", "two-spades"], not used yet
    human_cards: Optional[List[str]] = None
    computer_cards: Optional[List[str]] = None


def _make_card(rank_name: str, suit_name: str) -> Card:
    return Card(rank=Deck.RANKS[rank_name], suit=Deck.SUITS[suit_name])


def _generate_cards_for_ranks(ranks: List[str], n: int) -> List[Card]:
    suits = list(Deck.SUITS.keys())  # hearts, diamonds, clubs, spades
    cards: List[Card] = []
    i = 0
    while len(cards) < n:
        rank = ranks[i % len(ranks)]
        suit = suits[i % len(suits)]
        cards.append(_make_card(rank, suit))
        i += 1
    return cards


# In-memory game storage
games: Dict[str, GameSession] = {}


@app.get("/healthcheck")
def healthcheck():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/game/new")
def create_game(req: Optional[CreateGameRequest] = None) -> GameStateResponse:
    """Create a new game with optional deterministic setup."""
    game_id = str(uuid.uuid4())
    session = GameSession(game_id)

    # Configure dealer if specified
    if req and req.dealer:
        dealer_key = req.dealer.lower()
        if dealer_key in ("human", "you", "player"):
            session.next_dealer_override = session.human
        elif dealer_key == "computer":
            session.next_dealer_override = session.computer
        else:
            raise HTTPException(status_code=400, detail=f"Invalid dealer: {req.dealer}")

    # Configure preset hands if requested
    if req and req.preset:
        preset = req.preset
        if preset == 'aces_twos_vs_threes_fours':
            human_cards = _generate_cards_for_ranks(["ace", "two"], 6)
            computer_cards = _generate_cards_for_ranks(["three", "four"], 6)
            session.next_round_overrides = {
                'hands': {
                    session.human: human_cards,
                    session.computer: computer_cards,
                }
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unknown preset: {preset}")

    games[game_id] = session
    return session.advance()


@app.get("/game/{game_id}")
def get_game(game_id: str) -> GameStateResponse:
    """Get current game state."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    return games[game_id].get_state()


@app.post("/game/{game_id}/action")
def submit_action(game_id: str, action: PlayerAction) -> GameStateResponse:
    """Submit a player action."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    return games[game_id].submit_action(action.card_indices)


@app.delete("/game/{game_id}")
def delete_game(game_id: str):
    """Delete a game."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    del games[game_id]
    return {"status": "deleted"}
