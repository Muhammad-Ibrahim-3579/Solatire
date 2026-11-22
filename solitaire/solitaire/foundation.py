"""Foundation - one of the 4 suit piles. A Stack."""

from .pile import Pile, PileKind
from .stack import Stack


class Foundation(Pile):
    def __init__(self):
        self._cards = Stack()

    def kind(self):
        return PileKind.FOUNDATION

    def size(self):
        return self._cards.size()

    def top(self):
        return None if self._cards.is_empty() else self._cards.top()

    def push(self, card):
        self._cards.push(card)

    def pop(self):
        return self._cards.pop()

    def clear(self):
        self._cards.clear()
