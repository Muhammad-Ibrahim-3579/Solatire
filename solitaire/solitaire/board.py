"""Board - owns the deck, every pile and the card index.

    stock       Queue            waste        Stack
    foundations 4 x Stack        tableau      7 x DoublyLinkedList
    index       HashMap: card id -> CardInfo(pile, face_up)
"""

from . import algorithms as algo
from .deck import Deck
from .doubly_linked_list import DoublyLinkedList
from .foundation import Foundation
from .hash_map import HashMap
from .pile import PileKind, PileRef
from .rules import GameError
from .stack import Stack
from .stock import Stock, Waste
from .tableau import Tableau

COLUMNS = 7
FOUNDATIONS = 4


class CardInfo:
    __slots__ = ("pile", "face_up")

    def __init__(self, pile, face_up):
        self.pile = pile
        self.face_up = face_up


class Board:
    def __init__(self):
        self._deck = Deck()
        self._stock = Stock()
        self._waste = Waste()
        self._foundations = [Foundation() for _ in range(FOUNDATIONS)]
        self._tableau = [Tableau() for _ in range(COLUMNS)]
        self._index = HashMap()

    def deck(self):
        return self._deck

    def clear(self):
        self._stock.clear()
        self._waste.clear()
        for f in self._foundations:
            f.clear()
        for t in self._tableau:
            t.clear()
        self._index.clear()

    def deal(self):
        """Column c gets c+1 cards (only the last face up); 24 cards -> stock."""
        self.clear()
        for col in range(COLUMNS):
            ref = PileRef.tableau(col)
            for k in range(algo.column_size(col)):
                card = self._deck.at(algo.column_start(col) + k)
                card.face_up = algo.starts_face_up(col, k)
                self._tableau[col].push(card)
                self._index.put(card.id(), CardInfo(ref, card.face_up))
        for i in range(algo.STOCK_START, self._deck.size()):
            card = self._deck.at(i)
            card.face_up = False
            self._stock.enqueue(card)
            self._index.put(card.id(), CardInfo(PileRef.stock(), False))

    # ---------------------------------------------------------- queries
    def pile_size(self, ref):
        return self._pile(ref).size()

    def peek(self, ref):
        return self._pile(ref).top()

    def card_from_top(self, ref, n):
        """Tableau only. 1 = top card, 2 = the one below it ..."""
        self._check(ref)
        if ref.kind != PileKind.TABLEAU:
            raise GameError("only columns can be indexed")
        return self._tableau[ref.index].from_top(n)

    def count_face_up(self, ref):
        """Tableau only: how many cards at the top of the column are face up."""
        self._check(ref)
        if ref.kind != PileKind.TABLEAU:
            raise GameError("only columns can be indexed")
        t = self._tableau[ref.index]
        n = 0
        while n < t.size() and t.from_top(n + 1).face_up:
            n += 1
        return n

    def is_face_up(self, card):
        return self._index.get(card.id()).face_up

    def locate(self, card):
        return self._index.get(card.id()).pile

    def index_size(self):
        return self._index.size()

    def for_each_card(self, ref, fn):
        """Call fn(card) for a pile's cards: tableau/waste/foundation bottom to
        top, stock front to back. The pile is left exactly as it was."""
        self._check(ref)
        if ref.kind == PileKind.TABLEAU:
            t = self._tableau[ref.index]
            for i in range(t.size()):
                fn(t.at(i))
        elif ref.kind == PileKind.STOCK:
            for _ in range(self._stock.size()):  # rotate once around the queue
                card = self._stock.dequeue()
                fn(card)
                self._stock.enqueue(card)
        elif ref.kind == PileKind.WASTE:
            self._visit_stack(self._waste, fn)
        else:
            self._visit_stack(self._foundations[ref.index], fn)

    def cards_in(self, ref):
        """A Python list of a pile's cards (for drawing and tests)."""
        out = []
        self.for_each_card(ref, out.append)
        return out

    def snapshot(self):
        """One-line text picture of the whole board; tests compare these."""
        refs = [PileRef.stock(), PileRef.waste()]
        refs += [PileRef.foundation(i) for i in range(FOUNDATIONS)]
        refs += [PileRef.tableau(i) for i in range(COLUMNS)]
        parts = []
        for ref in refs:
            cards = " ".join(str(c) + ("^" if c.face_up else "v") for c in self.cards_in(ref))
            parts.append("%s:%s" % (ref, cards))
        return "|".join(parts)

    # -------------------------------------------------------- mutations
    def set_face_up(self, card, face_up):
        card.face_up = face_up
        self._index.get(card.id()).face_up = face_up

    def take_cards(self, ref, count, out):
        """Detach the top `count` cards of a pile into the list `out`."""
        self._check(ref)
        if ref.kind == PileKind.TABLEAU:
            self._tableau[ref.index].take_run(count, out)
            return
        if count != 1:
            raise GameError("only one card can leave this pile at a time")
        if ref.kind == PileKind.WASTE:
            out.push_back(self._waste.pop())
        elif ref.kind == PileKind.FOUNDATION:
            out.push_back(self._foundations[ref.index].pop())
        else:
            raise GameError("cards cannot be taken from the stock directly")

    def put_cards(self, ref, run):
        """Place a detached run on top of a pile; `run` ends up empty."""
        self._check(ref)
        for i in range(run.size()):
            self._index.get(run.at(i).id()).pile = ref
        if ref.kind == PileKind.TABLEAU:
            self._tableau[ref.index].put_run(run)
            return
        if run.size() != 1:
            raise GameError("only one card can enter this pile at a time")
        card = run.pop_back()
        if ref.kind == PileKind.FOUNDATION:
            self._foundations[ref.index].push(card)
        elif ref.kind == PileKind.WASTE:
            self._waste.push(card)
        else:
            raise GameError("cards cannot be placed on the stock directly")

    def draw_card(self):
        """Stock front -> waste top, turned face up."""
        card = self._stock.dequeue()
        self.set_face_up(card, True)
        self._waste.push(card)
        self._index.get(card.id()).pile = PileRef.waste()

    def return_drawn_card(self):
        """Exact reverse of draw_card."""
        card = self._waste.pop()
        self.set_face_up(card, False)
        self._stock.enqueue_front(card)
        self._index.get(card.id()).pile = PileRef.stock()

    def recycle_waste(self):
        """Turn the waste over into the (empty) stock. The cards pass through a
        temporary stack so the first card drawn last time is drawn first again."""
        temp = Stack()
        moved = 0
        while not self._waste.is_empty():
            card = self._waste.pop()
            self.set_face_up(card, False)
            temp.push(card)
            moved += 1
        while not temp.is_empty():
            card = temp.pop()
            self._stock.enqueue(card)
            self._index.get(card.id()).pile = PileRef.stock()
        return moved

    def restore_waste(self, count):
        """Exact reverse of recycle_waste."""
        for _ in range(count):
            card = self._stock.dequeue()
            self.set_face_up(card, True)
            self._waste.push(card)
            self._index.get(card.id()).pile = PileRef.waste()

    # ---------------------------------------------------------- private
    def _check(self, ref):
        if ref.kind == PileKind.TABLEAU and not 0 <= ref.index < COLUMNS:
            raise GameError("no such tableau column")
        if ref.kind == PileKind.FOUNDATION and not 0 <= ref.index < FOUNDATIONS:
            raise GameError("no such foundation")

    def _pile(self, ref):
        self._check(ref)
        if ref.kind == PileKind.STOCK:
            return self._stock
        if ref.kind == PileKind.WASTE:
            return self._waste
        if ref.kind == PileKind.FOUNDATION:
            return self._foundations[ref.index]
        return self._tableau[ref.index]

    @staticmethod
    def _visit_stack(pile, fn):
        temp = Stack()
        while not pile.is_empty():
            temp.push(pile.pop())  # reverses the order
        while not temp.is_empty():
            card = temp.pop()      # bottom card first
            fn(card)
            pile.push(card)
