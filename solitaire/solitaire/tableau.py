"""Tableau - one of the 7 columns: a doubly linked list.
Head = bottom card, tail = top card. Moving a run = split_back + append_list.
"""

from .doubly_linked_list import DoublyLinkedList
from .pile import Pile, PileKind


class Tableau(Pile):
    def __init__(self):
        self._cards = DoublyLinkedList()

    def kind(self):
        return PileKind.TABLEAU

    def size(self):
        return self._cards.size()

    def top(self):
        return None if self._cards.is_empty() else self._cards.back()

    def push(self, card):
        self._cards.push_back(card)

    def pop(self):
        return self._cards.pop_back()

    def at(self, i):
        """0 = bottom card."""
        return self._cards.at(i)

    def from_top(self, n):
        """1 = top card, 2 = the one below it ..."""
        return self._cards.at(self._cards.size() - n)

    def take_run(self, count, out):
        """Detach the top `count` cards into the list `out` (same order)."""
        self._cards.split_back(count, out)

    def put_run(self, run):
        """Put a detached run on top of this column; `run` ends up empty."""
        self._cards.append_list(run)

    def clear(self):
        self._cards.clear()
