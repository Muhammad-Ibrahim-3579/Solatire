"""Pile - how a pile is named (PileRef) and the abstract base class of all piles."""

from abc import ABC, abstractmethod
from enum import Enum


class PileKind(Enum):
    STOCK = "stock"
    WASTE = "waste"
    FOUNDATION = "foundation"
    TABLEAU = "tableau"


class PileRef:
    """Names a pile: its kind plus a number (column 0..6, foundation 0..3).

    Foundation i belongs to suit i (0 Hearts, 1 Diamonds, 2 Clubs, 3 Spades).
    """

    __slots__ = ("kind", "index")

    def __init__(self, kind, index=0):
        self.kind = kind
        self.index = index

    @staticmethod
    def stock():
        return PileRef(PileKind.STOCK, 0)

    @staticmethod
    def waste():
        return PileRef(PileKind.WASTE, 0)

    @staticmethod
    def foundation(i):
        return PileRef(PileKind.FOUNDATION, i)

    @staticmethod
    def tableau(i):
        return PileRef(PileKind.TABLEAU, i)

    def __eq__(self, other):
        return (isinstance(other, PileRef)
                and self.kind == other.kind and self.index == other.index)

    def __hash__(self):
        return hash((self.kind, self.index))

    def __str__(self):
        if self.kind == PileKind.TABLEAU:
            return "T%d" % (self.index + 1)
        if self.kind == PileKind.FOUNDATION:
            return "F%d" % (self.index + 1)
        return "S" if self.kind == PileKind.STOCK else "W"

    __repr__ = __str__


class Pile(ABC):
    """Every pile can say how many cards it holds and which card is on top."""

    @abstractmethod
    def kind(self):
        ...

    @abstractmethod
    def size(self):
        ...

    @abstractmethod
    def top(self):
        """The top card, or None when the pile is empty."""

    def is_empty(self):
        return self.size() == 0
