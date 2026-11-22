"""gui.py - the tkinter front end. It is a separate module: main.py imports it.

It only talks to the Game object (draw, move, move_to_foundation, undo, redo,
hint) and reads the board to draw it. No game rules live in this file.

Controls
    click the stock            draw (or recycle the waste)
    click a card, then a pile  move the card (and every card above it)
    drag a card onto a pile    same thing
    double-click a card        send it to its foundation
    Ctrl+Z / Ctrl+Y            undo / redo
    H hint, N new game, D or Space draw, Esc clear the selection
"""

import math
import time
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox

from solitaire.card import RANK_LABELS
from solitaire.game import Game
from solitaire.hint import DRAW, MOVE, RECYCLE
from solitaire.pile import PileKind, PileRef
from solitaire.rules import GameError

# ---- geometry ---------------------------------------------------------
CARD_W, CARD_H = 70, 96
GAP, MARGIN = 12, 16
TOP_Y = 14
TABLEAU_Y = TOP_Y + CARD_H + 22
DOWN_STEP, UP_STEP = 11, 25
WASTE_FAN = 18
CANVAS_W = 2 * MARGIN + 7 * CARD_W + 6 * GAP
CANVAS_H = TABLEAU_Y + 6 * DOWN_STEP + 12 * UP_STEP + CARD_H + 16
DRAG_THRESHOLD = 6

# ---- colours ----------------------------------------------------------
FELT = "#1b6b45"
SLOT = "#3f9467"
RED, BLACK = "#c62828", "#1c1c1c"
BACK_FILL, BACK_LINE = "#2f4f9e", "#8fa8e8"
SELECT, HINT = "#ffd54a", "#5ee0ff"
BAR = "#134d33"

SUIT_SYMBOLS = ("\u2665", "\u2666", "\u2663", "\u2660")  # hearts diamonds clubs spades


def column_x(i):
    """Left edge of column i (0-6); also used for the top row slots."""
    return MARGIN + i * (CARD_W + GAP)


def tableau_y_positions(cards):
    """Top edge of every card of a column (face-down cards overlap more)."""
    ys = []
    y = TABLEAU_Y
    for card in cards:
        ys.append(y)
        y += UP_STEP if card.face_up else DOWN_STEP
    return ys


class _Region:
    """A clickable rectangle that stands for a pile (and, for a card, a run).

    count is how many cards a click selects (the card and everything above it);
    None means the spot is only a drop target (face-down card, empty slot).
    """

    __slots__ = ("x0", "y0", "x1", "y1", "pile", "count")

    def __init__(self, x0, y0, x1, y1, pile, count):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.pile = pile
        self.count = count

    def contains(self, x, y):
        return self.x0 <= x < self.x1 and self.y0 <= y < self.y1


class SolitaireApp:
    def __init__(self, root=None, game=None):
        self.root = root if root is not None else tk.Tk()
        self.root.title("Klondike Solitaire")
        self.root.configure(bg=BAR)
        self.root.resizable(False, False)
        self.game = game if game is not None else Game(1)

        self._regions = []
        self._run_rects = {}
        self._pile_rects = {}
        self._selection = None      # (PileRef, count)
        self._press = None          # (x, y, region) of the last mouse press
        self._drag = None           # (PileRef, count, cards, grab_dx, grab_dy)
        self._hint = None
        self._hint_job = None
        self._message = "Click the stock to draw. Press H for a hint."
        self._message_is_error = False
        self._started = time.time()
        self._finished = None
        self.on_win = self._default_on_win  # tests replace this

        self._make_fonts()
        self._build_widgets()
        self._bind_events()
        self._redraw()
        self._tick()

    # ------------------------------------------------------------ setup
    def _make_fonts(self):
        families = set(tkfont.families(self.root))
        family = next((f for f in ("Segoe UI Symbol", "Segoe UI", "DejaVu Sans", "Arial")
                       if f in families), "TkDefaultFont")
        self._font_label = tkfont.Font(root=self.root, family=family, size=11, weight="bold")
        self._font_big = tkfont.Font(root=self.root, family=family, size=24)
        self._font_small = tkfont.Font(root=self.root, family=family, size=9)
        self._font_ui = tkfont.Font(root=self.root, family=family, size=10)

    def _build_widgets(self):
        bar = tk.Frame(self.root, bg=BAR)
        bar.pack(fill="x", padx=8, pady=6)

        self._draw_var = tk.IntVar(value=self.game.draw_count)
        self._btn_new = tk.Button(bar, text="New game", command=self.new_game)
        self._btn_undo = tk.Button(bar, text="Undo", command=self.undo)
        self._btn_redo = tk.Button(bar, text="Redo", command=self.redo)
        self._btn_hint = tk.Button(bar, text="Hint", command=self.show_hint)
        for button in (self._btn_new, self._btn_undo, self._btn_redo, self._btn_hint):
            button.configure(font=self._font_ui)
            button.pack(side="left", padx=2)
        for n in (1, 3):
            tk.Radiobutton(bar, text="Draw %d" % n, variable=self._draw_var, value=n,
                           command=self.new_game, bg=BAR, fg="white", selectcolor=BAR,
                           activebackground=BAR, activeforeground="white",
                           font=self._font_ui).pack(side="left", padx=4)

        self._stats = tk.Label(bar, text="", bg=BAR, fg="white", font=self._font_ui)
        self._stats.pack(side="right")

        self.canvas = tk.Canvas(self.root, width=CANVAS_W, height=CANVAS_H, bg=FELT,
                                highlightthickness=0)
        self.canvas.pack()

        self._status = tk.Label(self.root, text="", bg=BAR, fg="white", anchor="w",
                                font=self._font_ui)
        self._status.pack(fill="x", padx=8, pady=4)

    def _bind_events(self):
        c = self.canvas
        c.bind("<ButtonPress-1>", lambda e: self.press(e.x, e.y))
        c.bind("<B1-Motion>", lambda e: self.motion(e.x, e.y))
        c.bind("<ButtonRelease-1>", lambda e: self.release(e.x, e.y))
        c.bind("<Double-Button-1>", lambda e: self.double_click(e.x, e.y))
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Key-h>", lambda e: self.show_hint())
        self.root.bind("<Key-n>", lambda e: self.new_game())
        self.root.bind("<Key-d>", lambda e: self.draw())
        self.root.bind("<space>", lambda e: self.draw())
        self.root.bind("<Escape>", lambda e: self._clear_selection())

    def run(self):
        self.root.mainloop()

    # ---------------------------------------------------------- actions
    def new_game(self):
        self._clear_hint()
        self._selection = None
        self.game.new_game(self._draw_var.get())
        self._started = time.time()
        self._finished = None
        self._set_message("New game dealt.")
        self._redraw()

    def draw(self):
        self._act(self.game.draw)

    def undo(self):
        if not self.game.can_undo():
            self._set_message("Nothing to undo.", error=True)
            self._redraw()
            return
        self._act(self.game.undo)

    def redo(self):
        if not self.game.can_redo():
            self._set_message("Nothing to redo.", error=True)
            self._redraw()
            return
        self._act(self.game.redo)

    def show_hint(self):
        self._clear_hint()
        self._hint = self.game.hint()
        self._set_message("Hint: " + self._hint.message)
        self._redraw()
        self._hint_job = self.root.after(3500, self._hide_hint)

    def _act(self, action):
        """Run a game action, show a rule error if there is one, redraw."""
        self._clear_hint()
        try:
            action()
            self._set_message("")
        except GameError as error:
            self._set_message(str(error), error=True)
        self._selection = None
        self._update_clock_state()
        self._redraw()
        if self.game.is_won() and self._finished is not None and self._announce_pending:
            self._announce_pending = False
            self.on_win()

    _announce_pending = False

    def _update_clock_state(self):
        if self.game.is_won():
            if self._finished is None:
                self._finished = time.time()
                self._announce_pending = True
        else:
            self._finished = None
            self._announce_pending = False

    def _attempt_move(self, source, count, destination):
        if destination.kind == PileKind.FOUNDATION and count == 1:
            # whichever foundation was hit, send the card to its own suit's pile
            self._act(lambda: self.game.move_to_foundation(source))
        else:
            self._act(lambda: self.game.move(source, destination, count))

    def _default_on_win(self):
        text = "Moves: %d\nScore: %d\nTime: %s\n\nPlay again?" % (
            self.game.moves, self.game.score, self._format_time(self._elapsed()))
        if messagebox.askyesno("You won!", text, parent=self.root):
            self.new_game()

    # ------------------------------------------------------ mouse logic
    def _hit(self, x, y):
        for region in reversed(self._regions):
            if region.contains(x, y):
                return region
        return None

    def press(self, x, y):
        self._press = (x, y, self._hit(x, y))
        self._drag = None

    def motion(self, x, y):
        if self._press is None:
            return
        px, py, region = self._press
        if region is None or region.count is None or region.pile.kind == PileKind.STOCK:
            return
        if self._drag is None:
            if math.hypot(x - px, y - py) < DRAG_THRESHOLD:
                return
            cards = self.game.board.cards_in(region.pile)[-region.count:]
            self._drag = (region.pile, region.count, cards, px - region.x0, py - region.y0)
            self._selection = None
        _, _, cards, dx, dy = self._drag
        self.canvas.delete("ghost")
        for i, card in enumerate(cards):
            self._draw_card(x - dx, y - dy + i * UP_STEP, card, tag="ghost")

    def release(self, x, y):
        if self._press is None:
            return
        region = self._press[2]
        self._press = None
        if self._drag is not None:
            source, count, _, _, _ = self._drag
            self._drag = None
            self.canvas.delete("ghost")
            target = self._hit(x, y)
            if target is not None and target.pile != source:
                self._attempt_move(source, count, target.pile)
            else:
                self._redraw()
            return
        self._click(region)

    def double_click(self, x, y):
        self._press = None
        self._drag = None
        region = self._hit(x, y)
        if region is None:
            return
        if region.pile.kind == PileKind.STOCK:
            self._click(region)
        elif region.count == 1 and region.pile.kind != PileKind.FOUNDATION:
            source = region.pile
            self._act(lambda: self.game.move_to_foundation(source))

    def _click(self, region):
        if region is None:
            self._clear_selection()
            return
        pile = region.pile
        if pile.kind == PileKind.STOCK:
            self.draw()
            return
        if self._selection is not None and self._selection[0] != pile:
            source, count = self._selection
            self._attempt_move(source, count, pile)
            return
        if region.count is None:
            self._clear_selection()
            return
        chosen = (pile, region.count)
        self._selection = None if self._selection == chosen else chosen
        self._redraw()

    def _clear_selection(self):
        self._selection = None
        self._redraw()

    # ---------------------------------------------------------- hint ui
    def _hide_hint(self):
        self._hint_job = None
        self._hint = None
        self._redraw()

    def _clear_hint(self):
        if self._hint_job is not None:
            self.root.after_cancel(self._hint_job)
            self._hint_job = None
        self._hint = None

    # ---------------------------------------------------------- drawing
    def _redraw(self):
        self.canvas.delete("all")
        self._regions = []
        self._run_rects = {}
        self._pile_rects = {}
        board = self.game.board
        self._draw_top_row(board)
        self._draw_tableau(board)
        self._draw_hint()
        self._update_widgets()

    def _draw_top_row(self, board):
        # stock
        x = column_x(0)
        stock_count = board.pile_size(PileRef.stock())
        if stock_count > 0:
            self._draw_back(x, TOP_Y)
            self.canvas.create_text(x + CARD_W - 6, TOP_Y + CARD_H - 6, text=str(stock_count),
                                    anchor="se", fill="white", font=self._font_small)
        else:
            self._draw_slot(x, TOP_Y, "\u21bb" if board.pile_size(PileRef.waste()) else "")
        self._regions.append(_Region(x, TOP_Y, x + CARD_W, TOP_Y + CARD_H, PileRef.stock(), None))
        self._pile_rects["S"] = (x, TOP_Y, x + CARD_W, TOP_Y + CARD_H)

        # waste (draw-3 shows the last three cards fanned out)
        x = column_x(1)
        self._draw_slot(x, TOP_Y, "")
        waste = board.cards_in(PileRef.waste())
        shown = waste[-3:] if self.game.draw_count == 3 else waste[-1:]
        for i, card in enumerate(shown):
            is_top = i == len(shown) - 1
            selected = is_top and self._selection is not None and self._selection[0] == PileRef.waste()
            self._draw_card(x + i * WASTE_FAN, TOP_Y, card, selected)
            if is_top:
                rect = (x + i * WASTE_FAN, TOP_Y, x + i * WASTE_FAN + CARD_W, TOP_Y + CARD_H)
                self._regions.append(_Region(*rect, PileRef.waste(), 1))
                self._run_rects[("W", 1)] = rect
                self._pile_rects["W"] = rect

        # foundations
        for i in range(4):
            ref = PileRef.foundation(i)
            x = column_x(3 + i)
            self._draw_slot(x, TOP_Y, SUIT_SYMBOLS[i])
            cards = board.cards_in(ref)
            rect = (x, TOP_Y, x + CARD_W, TOP_Y + CARD_H)
            if cards:
                selected = self._selection is not None and self._selection[0] == ref
                self._draw_card(x, TOP_Y, cards[-1], selected)
                self._run_rects[(str(ref), 1)] = rect
            self._regions.append(_Region(*rect, ref, 1 if cards else None))
            self._pile_rects[str(ref)] = rect

    def _draw_tableau(self, board):
        for col in range(7):
            ref = PileRef.tableau(col)
            x = column_x(col)
            cards = board.cards_in(ref)
            # the whole column (and the space below it) is a drop target
            self._regions.append(_Region(x, TABLEAU_Y, x + CARD_W, CANVAS_H, ref, None))
            if not cards:
                self._draw_slot(x, TABLEAU_Y, "")
                self._pile_rects[str(ref)] = (x, TABLEAU_Y, x + CARD_W, TABLEAU_Y + CARD_H)
                continue
            ys = tableau_y_positions(cards)
            end_y = ys[-1] + CARD_H
            for row, card in enumerate(cards):
                count = len(cards) - row
                selected = (self._selection is not None and self._selection[0] == ref
                            and self._selection[1] >= count)
                self._draw_card(x, ys[row], card, selected)
                bottom = ys[row + 1] if row + 1 < len(cards) else end_y
                self._regions.append(
                    _Region(x, ys[row], x + CARD_W, bottom, ref, count if card.face_up else None))
                if card.face_up:
                    self._run_rects[(str(ref), count)] = (x, ys[row], x + CARD_W, end_y)
            self._pile_rects[str(ref)] = (x, ys[-1], x + CARD_W, end_y)

    def _draw_hint(self):
        hint = self._hint
        if hint is None:
            return
        rects = []
        if hint.type == MOVE:
            rects.append(self._run_rects.get((str(hint.source), hint.count)))
            rects.append(self._pile_rects.get(str(hint.destination)))
        elif hint.type in (DRAW, RECYCLE):
            rects.append(self._pile_rects.get("S"))
        for rect in rects:
            if rect is not None:
                self.canvas.create_rectangle(rect[0] - 2, rect[1] - 2, rect[2] + 2, rect[3] + 2,
                                             outline=HINT, width=4)

    def _round_rect(self, x0, y0, x1, y1, r=8, **options):
        points = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1,
                  x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
        return self.canvas.create_polygon(points, smooth=True, **options)

    def _draw_slot(self, x, y, symbol):
        self._round_rect(x, y, x + CARD_W, y + CARD_H, outline=SLOT, fill="", width=2, dash=(4, 3))
        if symbol:
            self.canvas.create_text(x + CARD_W // 2, y + CARD_H // 2, text=symbol,
                                    fill=SLOT, font=self._font_big)

    def _draw_back(self, x, y, tag=None):
        tags = (tag,) if tag else ()
        self._round_rect(x, y, x + CARD_W, y + CARD_H, fill=BACK_FILL, outline="white",
                         width=2, tags=tags)
        self.canvas.create_rectangle(x + 7, y + 7, x + CARD_W - 7, y + CARD_H - 7,
                                     outline=BACK_LINE, width=2, tags=tags)

    def _draw_card(self, x, y, card, selected=False, tag=None):
        if not card.face_up:
            self._draw_back(x, y, tag)
            return
        tags = (tag,) if tag else ()
        self._round_rect(x, y, x + CARD_W, y + CARD_H, fill="#fdfdfd",
                         outline=SELECT if selected else "#8a8a8a",
                         width=3 if selected else 1, tags=tags)
        color = RED if card.is_red() else BLACK
        symbol = SUIT_SYMBOLS[card.suit]
        self.canvas.create_text(x + 6, y + 4, text=RANK_LABELS[card.rank - 1] + symbol,
                                anchor="nw", fill=color, font=self._font_label, tags=tags)
        self.canvas.create_text(x + CARD_W - 8, y + CARD_H - 6, text=symbol, anchor="se",
                                fill=color, font=self._font_big, tags=tags)

    # ---------------------------------------------------------- status
    def _set_message(self, text, error=False):
        self._message = text
        self._message_is_error = error

    def _elapsed(self):
        end = self._finished if self._finished is not None else time.time()
        return end - self._started

    @staticmethod
    def _format_time(seconds):
        seconds = int(seconds)
        return "%d:%02d" % (seconds // 60, seconds % 60)

    def _update_widgets(self):
        self._btn_undo.configure(state=tk.NORMAL if self.game.can_undo() else tk.DISABLED)
        self._btn_redo.configure(state=tk.NORMAL if self.game.can_redo() else tk.DISABLED)
        self._draw_var.set(self.game.draw_count)
        self._status.configure(text=self._message or " ",
                               fg="#ffd0cc" if self._message_is_error else "white")
        self._refresh_stats()

    def _refresh_stats(self):
        self._stats.configure(text="Moves %d    Score %d    Time %s" % (
            self.game.moves, self.game.score, self._format_time(self._elapsed())))

    def _tick(self):
        self._refresh_stats()
        self.root.after(500, self._tick)
