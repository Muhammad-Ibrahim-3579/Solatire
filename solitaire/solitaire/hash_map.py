"""HashMap - separate chaining. Average O(1) put / get / erase.
Project use: where is each card (card id -> pile and face-up flag).
Each bucket holds a chain of nodes; when there are more entries than
buckets the table doubles (rehash) so the chains stay short.
"""


class _Node:
    __slots__ = ("key", "value", "next")

    def __init__(self, key, value, next_node):
        self.key = key
        self.value = value
        self.next = next_node


class HashMap:
    def __init__(self, initial_buckets=16):
        self._buckets = [None] * initial_buckets
        self._size = 0

    @staticmethod
    def _hash(key, bucket_count):
        return hash(key) % bucket_count

    def put(self, key, value):
        """Insert key -> value, or overwrite the value if key exists."""
        slot = self._hash(key, len(self._buckets))
        node = self._buckets[slot]
        while node is not None:
            if node.key == key:
                node.value = value
                return
            node = node.next
        self._buckets[slot] = _Node(key, value, self._buckets[slot])
        self._size += 1
        if self._size > len(self._buckets):
            self._rehash(len(self._buckets) * 2)

    def _find(self, key):
        node = self._buckets[self._hash(key, len(self._buckets))]
        while node is not None:
            if node.key == key:
                return node
            node = node.next
        return None

    def get(self, key):
        node = self._find(key)
        if node is None:
            raise KeyError(key)
        return node.value

    def contains(self, key):
        return self._find(key) is not None

    def erase(self, key):
        """Remove key. True if it was there, False otherwise."""
        slot = self._hash(key, len(self._buckets))
        previous = None
        node = self._buckets[slot]
        while node is not None:
            if node.key == key:
                if previous is None:
                    self._buckets[slot] = node.next
                else:
                    previous.next = node.next
                self._size -= 1
                return True
            previous = node
            node = node.next
        return False

    def clear(self):
        for i in range(len(self._buckets)):
            self._buckets[i] = None
        self._size = 0

    def size(self):
        return self._size

    def __len__(self):
        return self._size

    def _rehash(self, new_count):
        fresh = [None] * new_count
        for chain in self._buckets:
            node = chain
            while node is not None:
                nxt = node.next
                slot = self._hash(node.key, new_count)
                node.next = fresh[slot]
                fresh[slot] = node
                node = nxt
        self._buckets = fresh
