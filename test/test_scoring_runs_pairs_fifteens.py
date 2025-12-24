import pytest

from cribbage.cribbagegame import CribbageGame, CribbageRound
from cribbage.playingcards import Card, Deck
from cribbage.player import RandomPlayer


def make_card(rank: str, suit: str) -> Card:
    return Card(rank=Deck.RANKS[rank], suit=Deck.SUITS[suit])


def make_round() -> CribbageRound:
    game = CribbageGame(players=[RandomPlayer("player1"), RandomPlayer("player2")])
    return CribbageRound(game, dealer=game.players[0])


def test_hand_with_double_runs_pair_and_fifteens():
    """
    Hand: 5♠, 6♦, 7♠, 8♦, starter 7♦
    - Run of 4 (5,6,7♠,8): 4 points
    - Run of 4 using starter 7♦ (5,6,7♦,8): 4 points
    - Pair of 7s (7♠ and 7♦): 2 points
    - 7♠ + 8♦ = 15: 2 points
    - 7♦ + 8♦ = 15: 2 points
    Total: 14 points
    """
    round_inst = make_round()
    cards = [
        make_card("five", "spades"),
        make_card("six", "diamonds"),
        make_card("seven", "spades"),
        make_card("eight", "diamonds"),
        make_card("seven", "diamonds"),  # starter
    ]

    score = round_inst._score_hand(cards, is_crib=False)

    assert score == 14, f"Expected 14 points, got {score}"
