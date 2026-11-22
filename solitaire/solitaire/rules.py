"""Rules - Klondike validation, thin wrappers over algorithms.py."""

from . import algorithms as algo


class GameError(Exception):
    """Raised when a request breaks the rules of the game."""


class Rules:
    @staticmethod
    def can_place_on_tableau(card, top):
        """top is None for an empty column (only a King may go there)."""
        if top is None:
            return algo.can_place_on_tableau(card.rank, card.suit, 0, -1)
        return algo.can_place_on_tableau(card.rank, card.suit, top.rank, top.suit)

    @staticmethod
    def can_place_on_foundation(card, top):
        """top is None for an empty foundation (only an Ace may go there)."""
        if top is None:
            return algo.can_place_on_foundation(card.rank, card.suit, 0, -1)
        return algo.can_place_on_foundation(card.rank, card.suit, top.rank, top.suit)

    @staticmethod
    def is_valid_run(cards):
        """Cards bottom to top. A legal run has at most 13 cards."""
        if len(cards) > 13:
            return False
        return algo.is_valid_run([c.rank for c in cards], [c.suit for c in cards])
