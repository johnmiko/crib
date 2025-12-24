import pytest

from cribbage.cribbagegame import CribbageGame, CribbageRound
from cribbage.playingcards import Card, Deck
from cribbage.player import RandomPlayer


def make_card(rank: str, suit: str) -> Card:
    return Card(rank=Deck.RANKS[rank], suit=Deck.SUITS[suit])


def make_round() -> CribbageRound:
    game = CribbageGame(players=[RandomPlayer("player1"), RandomPlayer("player2")])
    return CribbageRound(game, dealer=game.players[0])


def test_hand_double_run_and_fifteens():
    """
    Hand: 5♠, 5♣, 6♦, 10♥, starter 4♠
    Expected:
    - Pair of 5s: 2
    - Fifteens (5+10 twice, and 4+5+6 twice): 8
    - Runs of 3 (4-5-6 twice): 6
    Total: 16 points
    """
    round_inst = make_round()
    cards = [
        make_card("five", "spades"),
        make_card("five", "clubs"),
        make_card("six", "diamonds"),
        make_card("ten", "hearts"),
        make_card("four", "spades"),  # starter
    ]

    score = round_inst._score_hand(cards, is_crib=False)
    assert score == 16, f"Expected 16 points, got {score}"