"""LinkedList - singly linked list. Indexes are 0-based; at/remove_at are O(n)."""


class _Node:
    __slots__ = ("value", "next")

    def __init__(self, value, next_node):
        self.value = value
        self.next = next_node


class LinkedList:
    def __init__(self):
        self._head = None
        self._tail = None
        self._size = 0

    def push_front(self, value):
        self._head = _Node(value, self._head)
        if self._tail is None:
            self._tail = self._head
        self._size += 1

    def push_back(self, value):
        node = _Node(value, None)
        if self._tail is None:
            self._head = node
        else:
            self._tail.next = node
        self._tail = node
        self._size += 1

    def pop_front(self):
        if self._head is None:
            raise IndexError("pop_front on empty LinkedList")
        node = self._head
        self._head = node.next
        if self._head is None:
            self._tail = None
        self._size -= 1
        return node.value

    def _node_at(self, index):
        if not 0 <= index < self._size:
            raise IndexError("LinkedList index out of range")
        node = self._head
        for _ in range(index):
            node = node.next
        return node

    def at(self, index):
        return self._node_at(index).value

    def remove_at(self, index):
        if not 0 <= index < self._size:
            raise IndexError("LinkedList index out of range")
        if index == 0:
            self.pop_front()
            return
        before = self._node_at(index - 1)
        victim = before.next
        before.next = victim.next
        if victim is self._tail:
            self._tail = before
        victim.next = None
        self._size -= 1

    def index_of(self, value):
        """Position of the first element equal to value, or -1."""
        node = self._head
        i = 0
        while node is not None:
            if node.value == value:
                return i
            node = node.next
            i += 1
        return -1

    def reverse(self):
        """Reverse in place by relinking the nodes."""
        previous = None
        node = self._head
        self._tail = self._head
        while node is not None:
            nxt = node.next
            node.next = previous
            previous = node
            node = nxt
        self._head = previous

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
