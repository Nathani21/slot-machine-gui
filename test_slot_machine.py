from slot_machine import (
    COLS,
    ROWS,
    check_winnings,
    format_result,
    get_spin,
    symbol_count,
    symbol_value,
)

# Boards are lists of columns: board[col][row]
NO_WIN = [["A", "B", "C"], ["B", "C", "D"], ["C", "D", "A"]]
TOP_ROW_WIN = [["A", "B", "C"], ["A", "C", "D"], ["A", "D", "B"]]
BOTTOM_ROW_WIN = [["B", "C", "A"], ["D", "B", "A"], ["C", "D", "A"]]


# get_spin
def test_spin_has_correct_shape():
    columns = get_spin()
    assert len(columns) == COLS
    assert all(len(column) == ROWS for column in columns)


def test_spin_only_uses_known_symbols():
    for _ in range(100):
        for column in get_spin():
            for symbol in column:
                assert symbol in symbol_count


def test_spin_never_exceeds_symbol_supply():
    for _ in range(100):
        for column in get_spin():
            for symbol in set(column):
                assert column.count(symbol) <= symbol_count[symbol]


def test_spin_does_not_change_symbol_count():
    before = dict(symbol_count)
    get_spin()
    assert symbol_count == before


# check_winnings
def test_no_winning_lines_returns_zero():
    winnings, win_lines = check_winnings(NO_WIN, 3, 10)
    assert winnings == 0
    assert win_lines == []


def test_winning_top_row_pays_something():
    winnings, _ = check_winnings(TOP_ROW_WIN, 1, 10)
    assert winnings > 0


def test_only_lines_bet_on_are_checked():
    winnings, _ = check_winnings(BOTTOM_ROW_WIN, 2, 10)
    assert winnings == 0


def test_bottom_row_counts_when_betting_on_all_lines():
    winnings, _ = check_winnings(BOTTOM_ROW_WIN, 3, 10)
    assert winnings > 0


def test_winning_line_pays_symbol_value_times_bet():
    winnings, _ = check_winnings(TOP_ROW_WIN, 1, 10)
    assert winnings == symbol_value["A"] * 10


def test_winning_lines_are_reported_one_based():
    _, win_lines = check_winnings(TOP_ROW_WIN, 3, 10)
    assert win_lines == [1]


def test_bottom_row_is_reported_as_line_three():
    winnings, win_lines = check_winnings(BOTTOM_ROW_WIN, 3, 10)
    assert win_lines == [3]
    assert winnings == symbol_value["A"] * 10


def test_multiple_winning_lines_add_up():
    board = [["A", "B", "A"], ["A", "B", "A"], ["A", "B", "A"]]
    winnings, win_lines = check_winnings(board, 3, 2)
    assert win_lines == [1, 2, 3]
    assert winnings == (symbol_value["A"] + symbol_value["B"] + symbol_value["A"]) * 2


def test_expected_return_is_close_to_but_below_the_bet():
    # Each cell is equally likely to be any symbol in the pool, so a row of
    # three matches with probability (count / pool size) ** COLS.
    total = sum(symbol_count.values())
    expected = sum(
        symbol_value[s] * (symbol_count[s] / total) ** COLS for s in symbol_count
    )
    assert 0.85 <= expected <= 1.0


def test_format_result_no_win():
    assert format_result(0, []) == "No win this time"


def test_format_result_single_line():
    assert format_result(50, [1]) == "You won $50 on line 1!"


def test_format_result_multiple_lines():
    assert format_result(75, [1, 3]) == "You won $75 on lines 1, 3!"