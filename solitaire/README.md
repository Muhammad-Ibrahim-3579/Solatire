# Klondike Solitaire - Python version

Same layers as the C++ project, with the GUI in its own file.

    python main.py                          start the game (needs Python 3.8+ with tkinter)
    python -m unittest discover -s tests -t . -v      run all tests

tkinter ships with the python.org installer on Windows and macOS. On Linux:
`sudo apt install python3-tk`. Without a screen the GUI tests are skipped.

## Files (one-to-one with the C++ headers)

| C++ header | Python module | Job |
|---|---|---|
| Vector.h | solitaire/vector.py | growable array (the 52-card deck) |
| Stack.h | solitaire/stack.py | linked stack: foundations, waste, undo history |
| Queue.h | solitaire/queue_.py | linked queue: the stock (named queue_ to avoid Python's own `queue`) |
| LinkedList.h | solitaire/linked_list.py | singly linked list |
| DoublyLinkedList.h | solitaire/doubly_linked_list.py | tableau columns |
| HashMap.h | solitaire/hash_map.py | card id -> pile and face-up flag |
| algorithms.h | solitaire/algorithms.py | shuffle, dealing positions, rules, win check |
| Card.h | solitaire/card.py | suit, rank, face up |
| Deck.h | solitaire/deck.py | 52 cards in a Vector |
| Pile.h | solitaire/pile.py | PileRef and the abstract Pile |
| Tableau.h / Foundation.h / Stock.h | solitaire/tableau.py, foundation.py, stock.py | the piles |
| Rules.h | solitaire/rules.py | placement rules, GameError |
| Board.h | solitaire/board.py | owns every pile and the card index |
| Command.h | solitaire/command.py | draw/recycle/move commands and History (undo/redo) |
| Hint.h | solitaire/hint.py | priority scan of legal moves |
| Game.h | solitaire/game.py | validates, runs commands, scores |
| (new) | gui.py | tkinter window; imports Game, holds no game rules |
| (new) | main.py | entry point; imports gui |
| test_main.cpp / test_game.cpp | tests/test_structures.py, tests/test_game.py | unittest versions |
| (new) | tests/test_gui.py | clicks, drags, double-click, hint through the real handlers |

No file in `solitaire/` imports tkinter, so the game logic can be tested and
reused without a window.

## Controls

click the stock = draw (recycles the waste when empty); click a card, then a
pile = move it (and every card above it); drag a card onto a pile = move;
double-click = send to its foundation; Ctrl+Z / Ctrl+Y = undo / redo;
H = hint; N = new game; D or Space = draw; Esc = clear the selection.
The Draw 1 / Draw 3 buttons start a new game in that mode.

## Python versus C++ differences

* Errors: IndexError replaces std::out_of_range; HashMap.get raises KeyError.
* Memory: nodes are freed by Python. Stack, Queue and the lists still unlink
  their nodes in a loop (clear / __del__) so a 200,000-node chain cannot
  overflow the call stack; the tests check it.
* Vector keeps its elements in a fixed-size list used like a raw array and
  doubles it by hand, so push_back is still amortised O(1).
