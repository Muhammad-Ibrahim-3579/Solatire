"""Deck - the 52 cards, stored in a Vector."""

from . import algorithms as algo
from .card import Card
from .vector import Vector

SIZE = 52


class Deck:
    def __init__(self):
        self._cards = Vector()
        self._cards.reserve(SIZE)
        for suit in range(4):
            for rank in range(1, 14):
                self._cards.push_back(Card(suit, rank))

    def shuffle(self, rng):
        
        algo.shuffle(self._cards, rng)

    def at(self, i):
        return self._cards[i]

    def size(self):
        return self._cards.size()

    def arrange_front(self, front_ids):
        
        used = [False] * SIZE
        order = []
        for card_id in front_ids:
            if not 0 <= card_id < SIZE or used[card_id]:
                raise ValueError("bad or duplicate card id")
            used[card_id] = True
            order.append(card_id)
        for card_id in range(SIZE):
            if not used[card_id]:
                order.append(card_id)
        for i in range(SIZE):
            self._cards[i] = Card(algo.suit_of_id(order[i]), algo.rank_of_id(order[i]))
