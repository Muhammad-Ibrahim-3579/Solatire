"""Command - undo/redo with the Command pattern.

Every action that changes the board is a Command object that can apply itself
(execute) and reverse itself (undo). History keeps two Stacks:
    undo stack: commands that have been applied
    redo stack: commands that were undone
A brand-new action empties the redo stack.
"""

from abc import ABC, abstractmethod

from .doubly_linked_list import DoublyLinkedList
from .pile import PileKind, PileRef
from .stack import Stack


class Command(ABC):
    @abstractmethod
    def execute(self):
        ...

    @abstractmethod
    def undo(self):
        ...

    def score_delta(self):
        """Score change caused by the last execute()."""
        return 0


class DrawCommand(Command):
    """Draw up to `count` cards from the stock onto the waste."""

    def __init__(self, board, count):
        self._board = board
        self._count = count
        self._drawn = 0

    def execute(self):
        available = self._board.pile_size(PileRef.stock())
        self._drawn = min(self._count, available)
        for _ in range(self._drawn):
            self._board.draw_card()

    def undo(self):
        for _ in range(self._drawn):
            self._board.return_drawn_card()


class RecycleCommand(Command):
    """Turn the waste back into the stock when the stock is empty."""

    def __init__(self, board):
        self._board = board
        self._moved = 0

    def execute(self):
        self._moved = self._board.recycle_waste()

    def undo(self):
        self._board.restore_waste(self._moved)

    def score_delta(self):
        return -20


class MoveCommand(Command):
    """Move `count` cards between piles and flip the card that gets uncovered."""

    def __init__(self, board, source, destination, count):
        self._board = board
        self._source = source
        self._destination = destination
        self._count = count
        self._revealed = None
        self._delta = 0

    def execute(self):
        run = DoublyLinkedList()
        self._board.take_cards(self._source, self._count, run)
        self._board.put_cards(self._destination, run)

        self._revealed = None
        if self._source.kind == PileKind.TABLEAU:
            new_top = self._board.peek(self._source)
            if new_top is not None and not self._board.is_face_up(new_top):
                self._board.set_face_up(new_top, True)
                self._revealed = new_top  # remember it, so undo can turn it back
        self._delta = self._compute_delta()

    def undo(self):
        if self._revealed is not None:
            self._board.set_face_up(self._revealed, False)
            self._revealed = None
        run = DoublyLinkedList()
        self._board.take_cards(self._destination, self._count, run)
        self._board.put_cards(self._source, run)

    def score_delta(self):
        return self._delta

    def _compute_delta(self):
        delta = 0
        if self._destination.kind == PileKind.FOUNDATION:
            delta += 10
        elif self._source.kind == PileKind.FOUNDATION:
            delta -= 15
        elif self._source.kind == PileKind.WASTE:
            delta += 5
        if self._revealed is not None:
            delta += 5
        return delta


class History:
    def __init__(self):
        self._undo = Stack()
        self._redo = Stack()

    def execute(self, command):
        """Run the command and keep it. Returns the score change."""
        command.execute()
        delta = command.score_delta()
        self._undo.push(command)
        self._redo.clear()  # a new action invalidates everything that was undone
        return delta

    def undo(self):
        """Reverse the latest command; returns it, or None if there is none."""
        if self._undo.is_empty():
            return None
        command = self._undo.pop()
        command.undo()
        self._redo.push(command)
        return command

    def redo(self):
        """Re-apply the most recently undone command, or None."""
        if self._redo.is_empty():
            return None
        command = self._redo.pop()
        command.execute()
        self._undo.push(command)
        return command

    def clear(self):
        self._undo.clear()
        self._redo.clear()

    def undo_depth(self):
        return self._undo.size()

    def redo_depth(self):
        return self._redo.size()
