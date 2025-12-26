"""Opponent strategies for computer players."""
import random
import numpy as np
import joblib
from abc import ABC, abstractmethod
from typing import List
from pathlib import Path
from itertools import combinations

from cribbage.playingcards import Card


class OpponentStrategy(ABC):
    """Base class for opponent decision-making strategies."""
    
    @abstractmethod
    def select_crib_cards(self, hand: List[Card]) -> List[Card]:
        """Select 2 cards to place in the crib.
        
        Args:
            hand: List of cards in the player's hand
            
        Returns:
            List of 2 cards to place in the crib
        """
        pass
    
    @abstractmethod
    def select_card_to_play(self, hand: List[Card], table: List[Card], table_value: int) -> Card:
        """Select a card to play from hand.
        
        Args:
            hand: List of cards in the player's hand
            table: List of cards on the table in current sequence
            table_value: Current table value (sum of card values)
            
        Returns:
            Card to play, or None if no valid play
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the display name for this opponent strategy."""
        pass


class RandomOpponent(OpponentStrategy):
    """Opponent that makes completely random decisions."""
    
    def select_crib_cards(self, hand: List[Card]) -> List[Card]:
        return random.sample(hand, 2)
    
    def select_card_to_play(self, hand: List[Card], table: List[Card], table_value: int) -> Card:
        # Filter to valid cards that won't exceed 31
        valid_cards = [c for c in hand if c.get_value() + table_value <= 31]
        if not valid_cards:
            return None
        return random.choice(valid_cards)
    
    def get_name(self) -> str:
        return "Random"


class GreedyOpponent(OpponentStrategy):
    """Opponent that tries to score points aggressively (placeholder for future implementation)."""
    
    def select_crib_cards(self, hand: List[Card]) -> List[Card]:
        # TODO: Implement greedy crib selection (keep high-scoring combinations)
        # For now, just use random selection
        return random.sample(hand, 2)
    
    def select_card_to_play(self, hand: List[Card], table: List[Card], table_value: int) -> Card:
        # TODO: Implement greedy play (prioritize 15s, pairs, runs)
        # For now, just use random selection
        valid_cards = [c for c in hand if c.get_value() + table_value <= 31]
        if not valid_cards:
            return None
        return random.choice(valid_cards)
    
    def get_name(self) -> str:
        return "Greedy (Not Implemented)"


class DefensiveOpponent(OpponentStrategy):
    """Opponent that plays defensively to minimize opponent's scoring (placeholder for future implementation)."""
    
    def select_crib_cards(self, hand: List[Card]) -> List[Card]:
        # TODO: Implement defensive crib selection
        # For now, just use random selection
        return random.sample(hand, 2)
    
    def select_card_to_play(self, hand: List[Card], table: List[Card], table_value: int) -> Card:
        # TODO: Implement defensive play (avoid giving opponent scoring opportunities)
        # For now, just use random selection
        valid_cards = [c for c in hand if c.get_value() + table_value <= 31]
        if not valid_cards:
            return None
        return random.choice(valid_cards)
    
    def get_name(self) -> str:
        return "Defensive (Not Implemented)"


class LinearBOpponent(OpponentStrategy):
    """Opponent using linear feature-based reinforcement learning model."""
    
    def __init__(self, model_date: str = "20251223"):
        """Initialize LinearB opponent with trained weights.
        
        Args:
            model_date: Date stamp of the model files to load (YYYYMMDD format)
        """
        models_dir = Path(__file__).parent.parent / "models" / "linear_b"
        
        throw_weights_path = models_dir / f"throw_weights_{model_date}.npy"
        peg_weights_path = models_dir / f"peg_weights_{model_date}.npy"
        
        try:
            self.throw_weights = np.load(throw_weights_path)
            self.peg_weights = np.load(peg_weights_path)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"LinearB model files not found: {e}")
    
    def _get_throwing_features(self, hand_cards: List[Card], thrown_cards: List[Card], is_dealer: bool) -> np.ndarray:
        """Extract 9-dimensional feature vector for throwing decision."""
        # Features: [lowCards, fives, highCards, tens, lowCardsThrown, fivesThrown, highCardsThrown, tensThrown, dealer]
        low_cards = sum(1 for c in hand_cards if c.get_value() < 5) / 4
        fives = sum(1 for c in hand_cards if c.get_value() == 5) / 4
        high_cards = sum(1 for c in hand_cards if 5 < c.get_value() < 10) / 4
        tens = sum(1 for c in hand_cards if c.get_value() == 10) / 4
        low_cards_thrown = sum(1 for c in thrown_cards if c.get_value() < 5) / 2
        fives_thrown = sum(1 for c in thrown_cards if c.get_value() == 5) / 2
        high_cards_thrown = sum(1 for c in thrown_cards if 5 < c.get_value() < 10) / 2
        tens_thrown = sum(1 for c in thrown_cards if c.get_value() == 10) / 2
        dealer = 1 if is_dealer else 0
        
        return np.array([low_cards, fives, high_cards, tens, low_cards_thrown, 
                        fives_thrown, high_cards_thrown, tens_thrown, dealer])
    
    def _get_pegging_features(self, hand_cards: List[Card], table_value: int, opponent_cards_left: int) -> np.ndarray:
        """Extract 7-dimensional feature vector for pegging decision."""
        # Features: [lowCards, fives, highCards, tens, countLow, countHigh, oppCards]
        low_cards = sum(1 for c in hand_cards if c.get_value() < 5) / 4
        fives = sum(1 for c in hand_cards if c.get_value() == 5) / 4
        high_cards = sum(1 for c in hand_cards if 5 < c.get_value() < 10) / 4
        tens = sum(1 for c in hand_cards if c.get_value() == 10) / 4
        count_low = 1 if table_value < 15 else 0
        count_high = 1 if table_value >= 15 else 0
        opp_cards = opponent_cards_left / 4
        
        return np.array([low_cards, fives, high_cards, tens, count_low, count_high, opp_cards])
    
    def select_crib_cards(self, hand: List[Card]) -> List[Card]:
        """Select cards to throw using linear model (simplified - assumes dealer)."""
        best_throw = None
        best_score = -np.inf
        
        # Evaluate all possible 2-card combinations
        for throw_combo in combinations(hand, 2):
            thrown = list(throw_combo)
            remaining = [c for c in hand if c not in thrown]
            
            # Simplified: assume we're dealer for AI training compatibility
            features = self._get_throwing_features(remaining, thrown, is_dealer=True)
            score = np.dot(self.throw_weights, features)
            
            if score > best_score:
                best_score = score
                best_throw = thrown
        
        return best_throw if best_throw else random.sample(hand, 2)
    
    def select_card_to_play(self, hand: List[Card], table: List[Card], table_value: int) -> Card:
        """Select card to play using linear pegging model."""
        valid_cards = [c for c in hand if c.get_value() + table_value <= 31]
        if not valid_cards:
            return None
        
        best_card = None
        best_score = -np.inf
        
        # Estimate opponent cards (simplified: assume 2 cards left)
        opponent_cards_left = 2
        
        for card in valid_cards:
            # Simulate playing this card
            new_hand = [c for c in hand if c != card]
            new_value = table_value + card.get_value()
            
            features = self._get_pegging_features(new_hand, new_value, opponent_cards_left)
            score = np.dot(self.peg_weights, features)
            
            if score > best_score:
                best_score = score
                best_card = card
        
        return best_card if best_card else random.choice(valid_cards)
    
    def get_name(self) -> str:
        return "LinearB"


class DeepPegOpponent(OpponentStrategy):
    """Opponent using deep neural network Q-learning model."""
    
    def __init__(self, model_date: str = "20251223"):
        """Initialize DeepPeg opponent with trained neural networks."""
        models_dir = Path(__file__).parent.parent / "models" / "deep_peg"
        
        pegging_brain_path = models_dir / f"pegging_brain_{model_date}.pkl"
        throwing_brain_path = models_dir / f"throwing_brain_{model_date}.pkl"
        
        try:
            self.pegging_brain = joblib.load(pegging_brain_path)
            self.throwing_brain = joblib.load(throwing_brain_path)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"DeepPeg model files not found: {e}")
    
    def _card_to_rank_value(self, card: Card) -> int:
        """Convert card to rank value (A=1, ..., K=13)."""
        rank_map = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
                    '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13}
        return rank_map.get(card.rank['name'], 0)
    
    def _get_throwing_state(self, hand: List[Card], thrown: List[Card], is_dealer: bool) -> np.ndarray:
        """Create 18-element state vector for throwing decision.
        
        Format: [hand_cards(4), thrown_cards(2), zeros(11), dealer(1)]
        """
        state = np.zeros(18)
        
        # Hand cards (sorted by rank)
        hand_ranks = sorted([self._card_to_rank_value(c) for c in hand])
        for i, rank in enumerate(hand_ranks[:4]):
            state[i] = rank
        
        # Thrown cards
        thrown_ranks = sorted([self._card_to_rank_value(c) for c in thrown])
        for i, rank in enumerate(thrown_ranks[:2]):
            state[4 + i] = rank
        
        # Dealer flag
        state[17] = 1 if is_dealer else 0
        
        return state.reshape(1, -1)
    
    def _get_pegging_state(self, hand: List[Card], table: List[Card], table_value: int, 
                          thrown: List[Card], is_dealer: bool) -> np.ndarray:
        """Create 18-element state vector for pegging decision.
        
        Format: [hand_cards(4), table_cards(8), thrown_cards(2), zeros(3), table_value(1/31), dealer(1)]
        """
        state = np.zeros(18)
        
        # Hand cards (sorted by rank)
        hand_ranks = sorted([self._card_to_rank_value(c) for c in hand])
        for i, rank in enumerate(hand_ranks[:4]):
            state[i] = rank
        
        # Table cards (most recent 8)
        table_ranks = [self._card_to_rank_value(c) for c in table[-8:]]
        for i, rank in enumerate(table_ranks):
            state[4 + i] = rank
        
        # Thrown cards
        thrown_ranks = sorted([self._card_to_rank_value(c) for c in thrown])
        for i, rank in enumerate(thrown_ranks[:2]):
            state[12 + i] = rank
        
        # Table value (normalized)
        state[16] = table_value / 31.0
        
        # Dealer flag
        state[17] = 1 if is_dealer else 0
        
        return state.reshape(1, -1)
    
    def select_crib_cards(self, hand: List[Card]) -> List[Card]:
        """Select cards to throw using neural network."""
        best_throw = None
        best_score = -np.inf
        
        for throw_combo in combinations(hand, 2):
            thrown = list(throw_combo)
            remaining = [c for c in hand if c not in thrown]
            
            state = self._get_throwing_state(remaining, thrown, is_dealer=True)
            
            try:
                score = self.throwing_brain.predict(state)[0]
            except:
                # If prediction fails, use random
                score = random.random()
            
            if score > best_score:
                best_score = score
                best_throw = thrown
        
        return best_throw if best_throw else random.sample(hand, 2)
    
    def select_card_to_play(self, hand: List[Card], table: List[Card], table_value: int) -> Card:
        """Select card to play using neural network."""
        valid_cards = [c for c in hand if c.get_value() + table_value <= 31]
        if not valid_cards:
            return None
        
        best_card = None
        best_score = -np.inf
        
        # Track thrown cards (simplified: empty for now)
        thrown = []
        
        for card in valid_cards:
            new_hand = [c for c in hand if c != card]
            new_table = table + [card]
            new_value = table_value + card.get_value()
            
            state = self._get_pegging_state(new_hand, new_table, new_value, thrown, is_dealer=True)
            
            try:
                score = self.pegging_brain.predict(state)[0]
            except:
                score = random.random()
            
            if score > best_score:
                best_score = score
                best_card = card
        
        return best_card if best_card else random.choice(valid_cards)
    
    def get_name(self) -> str:
        return "DeepPeg"


class MyrmidonOpponent(OpponentStrategy):
    """Opponent using Monte Carlo simulation heuristic (strongest baseline)."""
    
    def __init__(self):
        """Initialize Myrmidon opponent."""
        self.num_simulations = 10  # Number of Monte Carlo simulations per decision
    
    def select_crib_cards(self, hand: List[Card]) -> List[Card]:
        """Select cards using Monte Carlo simulation (simplified heuristic version)."""
        # For simplicity, use a heuristic approach:
        # Keep cards that work well together (pairs, runs, 15s)
        best_throw = None
        worst_hand_score = np.inf
        
        for throw_combo in combinations(hand, 2):
            thrown = list(throw_combo)
            remaining = [c for c in hand if c not in thrown]
            
            # Simple heuristic: minimize value of thrown cards, keep scoring potential
            throw_value = sum(c.get_value() for c in thrown)
            
            # Prefer keeping pairs and cards that sum to 15
            remaining_values = [c.get_value() for c in remaining]
            has_pair = len(remaining_values) != len(set(remaining_values))
            has_fifteen = any(
                remaining_values[i] + remaining_values[j] == 15
                for i in range(len(remaining_values))
                for j in range(i + 1, len(remaining_values))
            )
            
            # Score: lower is better (throw low-value cards, keep good cards)
            score = throw_value - (10 if has_pair else 0) - (10 if has_fifteen else 0)
            
            if score < worst_hand_score:
                worst_hand_score = score
                best_throw = thrown
        
        return best_throw if best_throw else random.sample(hand, 2)
    
    def select_card_to_play(self, hand: List[Card], table: List[Card], table_value: int) -> Card:
        """Select card using greedy heuristic."""
        valid_cards = [c for c in hand if c.get_value() + table_value <= 31]
        if not valid_cards:
            return None
        
        # Heuristic priorities:
        # 1. Try to make 15
        # 2. Try to make 31
        # 3. Try to pair the last card
        # 4. Avoid giving opponent good scoring opportunities
        
        for card in valid_cards:
            if table_value + card.get_value() == 15:
                return card
        
        for card in valid_cards:
            if table_value + card.get_value() == 31:
                return card
        
        if table and len(table) > 0:
            last_card = table[-1]
            for card in valid_cards:
                if card.get_value() == last_card.get_value():
                    return card
        
        # Otherwise, play card that gets closest to 15 or 31 without going over
        best_card = None
        best_distance = np.inf
        
        for card in valid_cards:
            new_value = table_value + card.get_value()
            # Prefer getting close to 15 or 31
            distance_to_15 = abs(15 - new_value) if new_value <= 15 else 100
            distance_to_31 = abs(31 - new_value)
            distance = min(distance_to_15, distance_to_31)
            
            if distance < best_distance:
                best_distance = distance
                best_card = card
        
        return best_card if best_card else random.choice(valid_cards)
    
    def get_name(self) -> str:
        return "Myrmidon"


# Registry of available opponents
OPPONENT_REGISTRY = {
    "random": RandomOpponent,
    "greedy": GreedyOpponent,
    "defensive": DefensiveOpponent,
    "linearb": LinearBOpponent,
    "deeppeg": DeepPegOpponent,
    "myrmidon": MyrmidonOpponent,
    # "bestai": BestAIOpponent,
}


def get_opponent_strategy(opponent_type: str = "random") -> OpponentStrategy:
    """Get an opponent strategy instance by type.
    
    Args:
        opponent_type: Type of opponent ("random", "greedy", "defensive")
        
    Returns:
        OpponentStrategy instance
        
    Raises:
        ValueError: If opponent_type is not recognized
    """
    if opponent_type not in OPPONENT_REGISTRY:
        raise ValueError(f"Unknown opponent type: {opponent_type}. Available: {list(OPPONENT_REGISTRY.keys())}")
    return OPPONENT_REGISTRY[opponent_type]()


def list_opponent_types() -> List[str]:
    """Get list of available opponent types."""
    return list(OPPONENT_REGISTRY.keys())
