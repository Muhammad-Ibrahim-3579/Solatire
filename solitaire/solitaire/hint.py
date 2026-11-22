"""Hint - scan every legal move once and keep the one with the highest
priority (first found wins a tie, so hints are repeatable).

    priority  move
      102     top card of a column with face-down cards below -> foundation
      100     waste card or other top card -> foundation
       80     a whole face-up run onto another column (uncovers a face-down card)
       60     waste card -> column
       50     a column that is entirely face up -> another column (empties it)
       10     draw from the stock
        5     recycle the waste
Pointless moves (a King column onto an empty column) are skipped.
"""

from .board import COLUMNS
from .pile import PileKind, PileRef
from .rules import Rules

NONE, MOVE, DRAW, RECYCLE = "none", "move", "draw", "recycle"


class Hint:
    def __init__(self):
        self.type = NONE
        self.source = PileRef.stock()
        self.destination = PileRef.stock()
        self.count = 0
        self.message = "No moves available. Try undo or a new game."


class HintFinder:
    @staticmethod
    def find(board):
        best = Hint()
        best_priority = [-1]  # a list so the helper below can change it

        def consider(priority, kind, source, destination, count, message):
            if priority > best_priority[0]:
                best_priority[0] = priority
                best.type = kind
                best.source = source
                best.destination = destination
                best.count = count
                best.message = message

        # 1. the waste card
        waste = board.peek(PileRef.waste())
        if waste is not None:
            foundation = PileRef.foundation(waste.suit)
            if Rules.can_place_on_foundation(waste, board.peek(foundation)):
                consider(100, MOVE, PileRef.waste(), foundation, 1,
                         _describe(waste, 1, PileRef.waste(), foundation))
            for j in range(COLUMNS):
                dest = PileRef.tableau(j)
                if Rules.can_place_on_tableau(waste, board.peek(dest)):
                    consider(60, MOVE, PileRef.waste(), dest, 1,
                             _describe(waste, 1, PileRef.waste(), dest))

        # 2. cards in the columns
        for i in range(COLUMNS):
            source = PileRef.tableau(i)
            size = board.pile_size(source)
            if size == 0:
                continue
            face_up = board.count_face_up(source)

            top = board.peek(source)
            foundation = PileRef.foundation(top.suit)
            if Rules.can_place_on_foundation(top, board.peek(foundation)):
                priority = 102 if face_up < size else 100
                consider(priority, MOVE, source, foundation, 1,
                         _describe(top, 1, source, foundation))

            for run in range(1, face_up + 1):
                lead = board.card_from_top(source, run)
                reveals = run == face_up and face_up < size
                empties_column = run == size
                for j in range(COLUMNS):
                    if j == i:
                        continue
                    dest = PileRef.tableau(j)
                    target = board.peek(dest)
                    if not Rules.can_place_on_tableau(lead, target):
                        continue
                    if lead.rank == 13 and target is None and empties_column:
                        continue
                    if reveals:
                        consider(80, MOVE, source, dest, run,
                                 _describe(lead, run, source, dest))
                    elif empties_column:
                        consider(50, MOVE, source, dest, run,
                                 _describe(lead, run, source, dest))

        # 3. fall back to the stock
        if board.pile_size(PileRef.stock()) > 0:
            consider(10, DRAW, PileRef.stock(), PileRef.waste(), 0, "Draw from the stock.")
        elif board.pile_size(PileRef.waste()) > 0:
            consider(5, RECYCLE, PileRef.waste(), PileRef.stock(), 0,
                     "Recycle the waste pile into the stock.")
        return best


def _describe(lead, count, source, destination):
    text = "Move %s" % lead
    if count > 1:
        text += " (and %d more)" % (count - 1)
    text += " from %s to " % source
    text += "its foundation" if destination.kind == PileKind.FOUNDATION else str(destination)
    return text + "."
