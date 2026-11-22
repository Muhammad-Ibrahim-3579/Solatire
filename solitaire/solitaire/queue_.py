"""Queue - FIFO, linked nodes with head and tail pointers.
(File is named queue_ so it never clashes with Python's own `queue` module.)
Project use: the stock (draw) pile.
"""


class _Node:
    __slots__ = ("value", "next")

    def __init__(self, value, next_node):
        self.value = value
        self.next = next_node


class Queue:
    def __init__(self):
        self._head = None
        self._tail = None
        self._size = 0

    def enqueue(self, value):
        node = _Node(value, None)
        if self._tail is None:
            self._head = node
        else:
            self._tail.next = node
        self._tail = node
        self._size += 1

    def enqueue_front(self, value):
        """Put value at the FRONT (next to leave). Used to undo a draw."""
        self._head = _Node(value, self._head)
        if self._tail is None:
            self._tail = self._head
        self._size += 1

    def dequeue(self):
        if self._head is None:
            raise IndexError("dequeue from empty Queue")
        node = self._head
        self._head = node.next
        if self._head is None:
            self._tail = None  # the classic bug: forgetting this line
        self._size -= 1
        return node.value

    def front(self):
        if self._head is None:
            raise IndexError("front of empty Queue")
        return self._head.value

    def clear(self):
        node = self._head
        while node is not None:
            nxt = node.next
            node.next = None
            node = nxt
        self._head = None
        self._tail = None
        self._size = 0

    def is_empty(self):
        return self._size == 0

    def size(self):
        return self._size

    def __len__(self):
        return self._size

    def __del__(self):
        self.clear()
