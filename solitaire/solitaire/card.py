"""Card - one playing card (suit 0-3, rank 1-13, face up or down)."""

from . import algorithms as algo

RANK_LABELS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
SUIT_LETTERS = "HDCS"


class Card:
    __slots__ = ("suit", "rank", "face_up")

    def __init__(self, suit=0, rank=1):
        self.suit = suit
        self.rank = rank
        self.face_up = False

    def id(self):
        return algo.make_id(self.suit, self.rank)

    def is_red(self):
        return algo.is_red(self.suit)

    def __str__(self):
        return RANK_LABELS[self.rank - 1] + SUIT_LETTERS[self.suit]

    __repr__ = __str__
