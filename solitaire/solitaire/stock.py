"""Stock (face-down draw pile, a Queue) and Waste (face-up discard, a Stack)."""

from .pile import Pile, PileKind
from .queue_ import Queue
from .stack import Stack


class Stock(Pile):
    """Cards leave in the order they were dealt: first in, first out."""

    def __init__(self):
        self._cards = Queue()

    def kind(self):
        return PileKind.STOCK

    def size(self):
        return self._cards.size()

    def top(self):
        return None if self._cards.is_empty() else self._cards.front()

    def enqueue(self, card):
        self._cards.enqueue(card)

    def enqueue_front(self, card):
        """Used by undo."""
        self._cards.enqueue_front(card)

    def dequeue(self):
        return self._cards.dequeue()

    def clear(self):
        self._cards.clear()


class Waste(Pile):
    """Only the top card is playable: last in, first out."""

    def __init__(self):
        self._cards = Stack()

    def kind(self):
        return PileKind.WASTE

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
