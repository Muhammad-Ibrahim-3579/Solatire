"""
Card convention used everywhere:
    suit: 0 = Hearts, 1 = Diamonds, 2 = Clubs, 3 = Spades
    rank: 1 = Ace ... 11 = Jack, 12 = Queen, 13 = King
    card id: suit * 13 + (rank - 1)        (0..51)
"""


def suit_of_id(card_id):
    return card_id // 13


def rank_of_id(card_id):
    return card_id % 13 + 1


def make_id(suit, rank):
    return suit * 13 + (rank - 1)


def is_red(suit):
    return suit == 0 or suit == 1




def shuffle(data, rng):
 
    n = len(data)
    for i in range(n - 1, 0, -1):
        j = rng.randint(0, i)
        data[i], data[j] = data[j], data[i]


# After shuffling column 0 gets 1 card column 1 gets 2 and hence column 6 gets 7.
# The remaining 24 cards form the stock.
COLUMNS = 7
STOCK_START = 28 


def column_start(col):
    """Index in the shuffled deck of the first (bottom) card of a column."""
    return col * (col + 1) // 2


def column_size(col):
    return col + 1


def starts_face_up(col, position_in_column):
    """Only the last card dealt to a column starts face up."""
    return position_in_column == col


# ---- move rules 
# top_rank == 0 means "the pile is empty.


def can_place_on_tableau(rank, suit, top_rank, top_suit):
    """King on an empty column; otherwise one rank lower and opposite colour."""
    if top_rank == 0:
        return rank == 13
    return is_red(suit) != is_red(top_suit) and rank == top_rank - 1


def can_place_on_foundation(rank, suit, top_rank, top_suit):
    """Ace first, then one rank higher in the same suit."""
    if top_rank == 0:
        return rank == 1
    return suit == top_suit and rank == top_rank + 1


def is_valid_run(ranks, suits):
    """Cards bottom to top: ranks fall by one and colours alternate. O(n)."""
    for i in range(1, len(ranks)):
        if is_red(suits[i]) == is_red(suits[i - 1]):
            return False
        if ranks[i] != ranks[i - 1] - 1:
            return False
    return True




def is_won(foundation_sizes):
    """Won when all four foundations hold 13 cards."""
    if len(foundation_sizes) != 4:
        return False
    for size in foundation_sizes:
        if size != 13:
            return False
    return True
