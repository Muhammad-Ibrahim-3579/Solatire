"""Game - the game controller: deals, validates every request against the
rules, runs it through History (so it can be undone) and keeps the score.
No input, output or GUI code in here: any front end can sit on top of it.
"""

import random

from .board import Board
from .command import DrawCommand, History, MoveCommand, RecycleCommand
from .hint import HintFinder
from .pile import PileKind, PileRef
from .rules import GameError, Rules
from . import algorithms as algo


class Game:
    def __init__(self, draw_count=1, seed=None):
        self._rng = random.Random(seed)
        self._board = Board()
        self._history = History()
        self._draw_count = 1
        self._score = 0
        self._set_draw_count(draw_count)
        self.new_game()

    def new_game(self, draw_count=0):
        """draw_count 0 keeps the current mode (1 or 3 cards per draw)."""
        if draw_count != 0:
            self._set_draw_count(draw_count)
        self._board.clear()
        self._board.deck().shuffle(self._rng)
        self._start()

    def new_game_with_front(self, ids):
        """For tests: deal with these card ids on the front of the deck."""
        self._board.clear()
        self._board.deck().arrange_front(ids)
        self._start()

    # ---------------------------------------------------------- actions
    def draw(self):
        """Draw from the stock, or recycle the waste when the stock is empty."""
        if self._board.pile_size(PileRef.stock()) > 0:
            self._score += self._history.execute(DrawCommand(self._board, self._draw_count))
        elif self._board.pile_size(PileRef.waste()) > 0:
            self._score += self._history.execute(RecycleCommand(self._board))
        else:
            raise GameError("The stock and waste are both empty.")

    def move(self, source, destination, count=1):
        self._validate_move(source, destination, count)
        self._score += self._history.execute(
            MoveCommand(self._board, source, destination, count))

    def move_to_foundation(self, source):
        """Top card of `source` to the foundation of its own suit."""
        card = self._board.peek(source)
        if card is None:
            raise GameError("The source pile is empty.")
        self.move(source, PileRef.foundation(card.suit), 1)

    def undo(self):
        command = self._history.undo()
        if command is None:
            return False
        self._score -= command.score_delta()
        return True

    def redo(self):
        command = self._history.redo()
        if command is None:
            return False
        self._score += command.score_delta()
        return True

    # ---------------------------------------------------------- queries
    def is_won(self):
        sizes = [self._board.pile_size(PileRef.foundation(i)) for i in range(4)]
        return algo.is_won(sizes)

    def hint(self):
        return HintFinder.find(self._board)

    @property
    def board(self):
        return self._board

    @property
    def draw_count(self):
        return self._draw_count

    @property
    def score(self):
        return self._score

    @property
    def moves(self):
        return self._history.undo_depth()

    def can_undo(self):
        return self._history.undo_depth() > 0

    def can_redo(self):
        return self._history.redo_depth() > 0

    # ---------------------------------------------------------- private
    def _set_draw_count(self, draw_count):
        if draw_count not in (1, 3):
            raise GameError("Draw count must be 1 or 3.")
        self._draw_count = draw_count

    def _start(self):
        self._board.deal()
        self._history.clear()
        self._score = 0

    def _validate_move(self, source, destination, count):
        board = self._board
        if source.kind == PileKind.STOCK:
            raise GameError("Use draw to take cards from the stock.")
        if destination.kind in (PileKind.STOCK, PileKind.WASTE):
            raise GameError("Cards cannot be placed there.")
        if source == destination:
            raise GameError("Source and destination must differ.")
        if count < 1:
            raise GameError("Count must be at least 1.")
        if source.kind != PileKind.TABLEAU and count != 1:
            raise GameError("Only one card can leave that pile.")
        if destination.kind == PileKind.FOUNDATION and count != 1:
            raise GameError("Foundations accept one card at a time.")
        available = board.pile_size(source)
        board.pile_size(destination)  # also validates the destination address
        if available == 0:
            raise GameError("The source pile is empty.")
        if count > available:
            raise GameError("The source pile only holds %d card(s)." % available)
        if count > 13:
            raise GameError("A run has at most 13 cards.")

        # the cards being moved, bottom to top
        if source.kind == PileKind.TABLEAU:
            run = [board.card_from_top(source, count - k) for k in range(count)]
        else:
            run = [board.peek(source)]
        for card in run:
            if not board.is_face_up(card):
                raise GameError("Face-down cards cannot be moved.")
        if not Rules.is_valid_run(run):
            raise GameError("Moved cards must descend in rank and alternate in colour.")

        lead = run[0]
        target = board.peek(destination)
        if destination.kind == PileKind.FOUNDATION:
            if lead.suit != destination.index:
                raise GameError("%s belongs on foundation F%d." % (lead, lead.suit + 1))
            if not Rules.can_place_on_foundation(lead, target):
                raise GameError("%s cannot go on the foundation yet." % lead)
        elif not Rules.can_place_on_tableau(lead, target):
            raise GameError("%s cannot be placed on that column." % lead)
