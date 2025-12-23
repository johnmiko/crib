"""Pytest configuration and fixtures.

Ensures the crib project directory is in the Python path so imports work correctly.
"""

import sys
from pathlib import Path
import pytest

from cribbage.player import RandomPlayer as _RandomPlayer

# Add the project root to sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def deterministic_computer(monkeypatch):
	"""Monkeypatch the computer's card selection to be deterministic.

	Strategy:
	- Prefer playing a card that makes the count exactly 15
	- Otherwise prefer making a pair with the last card on the table
	- Otherwise play the first valid card that keeps count <= 31
	This reduces flakiness in tests that depend on the computer's move.
	"""

	def _select_card(self, hand, table, crib):
		table_value = sum(m['card'].get_value() for m in table)
		valid = [c for c in hand if c.get_value() + table_value <= 31]
		if not valid:
			return None
		for c in valid:
			if c.get_value() + table_value == 15:
				return c
		if table:
			last_rank = table[-1]['card'].get_rank()
			for c in valid:
				if c.get_rank() == last_rank:
					return c
		return valid[0]

	monkeypatch.setattr(_RandomPlayer, "select_card_to_play", _select_card, raising=True)
	return True
