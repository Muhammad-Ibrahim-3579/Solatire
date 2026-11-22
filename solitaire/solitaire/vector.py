"""Vector - a growable array.

The storage is a fixed-size Python list used like a raw array
([None] * capacity). It never grows by itself: push_back allocates a bigger
array (double the capacity), copies the elements over and drops the old one,
so push_back is amortised O(1).
Project use: the deck of 52 cards.
"""


class Vector:
    def __init__(self):
        self._data = []
        self._size = 0
        self._capacity = 0

    def push_back(self, value):
        if self._size == self._capacity:
            self.reserve(4 if self._capacity == 0 else self._capacity * 2)
        self._data[self._size] = value
        self._size += 1

    def pop_back(self):
        if self._size == 0:
            raise IndexError("pop_back on empty Vector")
        self._size -= 1
        self._data[self._size] = None

    def at(self, index):
        if not 0 <= index < self._size:
            raise IndexError("Vector index out of range")
        return self._data[index]

    def __getitem__(self, index):
        return self.at(index)

    def __setitem__(self, index, value):
        if not 0 <= index < self._size:
            raise IndexError("Vector index out of range")
        self._data[index] = value

    def reserve(self, new_capacity):
        """Make room for new_capacity elements without changing size()."""
        if new_capacity <= self._capacity:
            return
        fresh = [None] * new_capacity
        for i in range(self._size):
            fresh[i] = self._data[i]
        self._data = fresh
        self._capacity = new_capacity

    def clear(self):
        for i in range(self._size):
            self._data[i] = None
        self._size = 0

    def size(self):
        return self._size

    def capacity(self):
        return self._capacity

    def is_empty(self):
        return self._size == 0

    def __len__(self):
        return self._size

    def __iter__(self):
        for i in range(self._size):
            yield self._data[i]
