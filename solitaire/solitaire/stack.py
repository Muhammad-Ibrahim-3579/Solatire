"""Stack - LIFO, built from linked nodes. push/pop/top are O(1).
Project use: foundation piles, the waste pile, undo/redo history.
"""


class _Node:
    __slots__ = ("value", "next")

    def __init__(self, value, next_node):
        self.value = value
        self.next = next_node


class Stack:
    def __init__(self):
        self._top = None
        self._size = 0

    def push(self, value):
        self._top = _Node(value, self._top)
        self._size += 1

    def pop(self):
        if self._top is None:
            raise IndexError("pop from empty Stack")
        node = self._top
        self._top = node.next
        self._size -= 1
        return node.value

    def top(self):
        if self._top is None:
            raise IndexError("top of empty Stack")
        return self._top.value

    def clear(self):
        # a loop, not recursion: a long chain must not overflow the call stack
        node = self._top
        while node is not None:
            nxt = node.next
            node.next = None
            node = nxt
        self._top = None
        self._size = 0

    def is_empty(self):
        return self._size == 0

    def size(self):
        return self._size

    def __len__(self):
        return self._size

    def __del__(self):
        self.clear()
