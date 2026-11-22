"""DoublyLinkedList - nodes with next AND prev pointers.
Project use: one tableau column (head = bottom card, tail = top card).
split_back / append_list MOVE nodes by relinking; no node is copied, which is
what makes moving a run of cards cheap.
"""


class _Node:
    __slots__ = ("value", "prev", "next")

    def __init__(self, value, prev, next_node):
        self.value = value
        self.prev = prev
        self.next = next_node


class DoublyLinkedList:
    def __init__(self):
        self._head = None
        self._tail = None
        self._size = 0

    def push_back(self, value):
        node = _Node(value, self._tail, None)
        if self._tail is None:
            self._head = node
        else:
            self._tail.next = node
        self._tail = node
        self._size += 1

    def pop_back(self):
        node = self._tail
        if node is None:
            raise IndexError("pop_back on empty DoublyLinkedList")
        self._tail = node.prev
        if self._tail is None:
            self._head = None
        else:
            self._tail.next = None
        node.prev = None
        self._size -= 1
        return node.value

    def back(self):
        if self._tail is None:
            raise IndexError("back of empty DoublyLinkedList")
        return self._tail.value

    def at(self, index):
        if not 0 <= index < self._size:
            raise IndexError("DoublyLinkedList index out of range")
        node = self._head
        for _ in range(index):
            node = node.next
        return node.value

    def split_back(self, count, target):
        """Detach the LAST count nodes and append them, in order, to target.

        1 <= count <= size() or IndexError (nothing changes).
        Example: self=[1,2,3,4], target=[9]; split_back(2, target)
                 -> self=[1,2], target=[9,3,4]
        """
        if not 1 <= count <= self._size:
            raise IndexError("split_back count out of range")
        first = self._tail
        for _ in range(count - 1):
            first = first.prev
        before = first.prev
        last_moved = self._tail

        self._tail = before
        if before is None:
            self._head = None
        else:
            before.next = None
        self._size -= count

        first.prev = target._tail
        if target._tail is None:
            target._head = first
        else:
            target._tail.next = first
        target._tail = last_moved
        target._size += count

    def append_list(self, other):
        """Move ALL nodes of other onto the end of this list; other is emptied."""
        if other._head is None:
            return
        if self._tail is None:
            self._head = other._head
        else:
            self._tail.next = other._head
            other._head.prev = self._tail
        self._tail = other._tail
        self._size += other._size
        other._head = None
        other._tail = None
        other._size = 0

    def clear(self):
        node = self._head
        while node is not None:
            nxt = node.next
            node.next = None
            node.prev = None
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
