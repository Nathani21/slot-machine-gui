import tkinter as tk

import pytest

import slot_machine
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

# GUI
@pytest.fixture(scope="session")
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f"Tk is not available here: {error}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def app(tk_root):
    window = tk.Toplevel(tk_root)
    window.withdraw()
    yield slot_machine.SlotMachine(window)
    window.destroy()


@pytest.fixture
def popups(monkeypatch):
    shown = []
    monkeypatch.setattr(
        slot_machine.messagebox, "showerror", lambda title, msg: shown.append(("error", msg))
    )
    monkeypatch.setattr(
        slot_machine.messagebox, "showinfo", lambda title, msg: shown.append(("info", msg))
    )
    return shown


def set_inputs(app, lines, bet):
    app.lines_entry.delete(0, tk.END)
    app.lines_entry.insert(0, str(lines))
    app.bet_entry.delete(0, tk.END)
    app.bet_entry.insert(0, str(bet))


def force_board(monkeypatch, board):
    monkeypatch.setattr(slot_machine, "get_spin", lambda: board)


def test_app_starts_ready(app):
    assert app.balance == slot_machine.STARTING_BALANCE
    assert app.result_label.cget("text") == slot_machine.READY_TEXT
    assert str(app.spin_btn.cget("state")) == "normal"
    assert str(app.new_game_btn.cget("state")) == "disabled"


def test_losing_spin_charges_the_bet(app, popups, monkeypatch):
    force_board(monkeypatch, NO_WIN)
    set_inputs(app, 2, 10)
    app.spin()
    assert app.balance == slot_machine.STARTING_BALANCE - 20
    assert app.result_label.cget("text") == "No win this time"
    assert popups == []


def test_winning_spin_pays_and_highlights_the_row(app, popups, monkeypatch):
    force_board(monkeypatch, TOP_ROW_WIN)
    set_inputs(app, 1, 10)
    app.spin()
    win = symbol_value["A"] * 10
    assert app.balance == slot_machine.STARTING_BALANCE + win - 10
    assert app.result_label.cget("text") == format_result(win, [1])
    assert [label.cget("text") for label in app.slot_labels[0]] == ["A", "A", "A"]
    for label in app.slot_labels[0]:
        assert label.cget("bg") == slot_machine.COLOR_GOLD
    for label in app.slot_labels[1] + app.slot_labels[2]:
        assert label.cget("bg") == slot_machine.COLOR_CREAM
    assert popups == []


def test_highlight_clears_on_the_next_spin(app, popups, monkeypatch):
    set_inputs(app, 1, 1)
    force_board(monkeypatch, TOP_ROW_WIN)
    app.spin()
    force_board(monkeypatch, NO_WIN)
    app.spin()
    for row in app.slot_labels:
        for label in row:
            assert label.cget("bg") == slot_machine.COLOR_CREAM


@pytest.mark.parametrize(
    "lines, bet",
    [("abc", "1"), ("1", "x"), ("0", "1"), ("4", "1"), ("1", "0"), ("1", "101")],
)
def test_invalid_input_shows_an_error_and_does_not_spin(app, popups, lines, bet):
    set_inputs(app, lines, bet)
    app.spin()
    assert len(popups) == 1
    assert popups[0][0] == "error"
    assert app.balance == slot_machine.STARTING_BALANCE


def test_not_enough_balance_shows_an_error(app, popups):
    set_inputs(app, 3, 100)
    app.spin()
    assert popups == [("error", "Not enough balance!")]
    assert app.balance == slot_machine.STARTING_BALANCE


def test_game_over_then_new_game(app, popups, monkeypatch):
    force_board(monkeypatch, NO_WIN)
    set_inputs(app, 1, 100)
    app.spin()
    assert app.balance == 0
    assert str(app.spin_btn.cget("state")) == "disabled"
    assert str(app.new_game_btn.cget("state")) == "normal"
    assert popups[-1][0] == "info"

    app.new_game()
    assert app.balance == slot_machine.STARTING_BALANCE
    assert app.result_label.cget("text") == slot_machine.READY_TEXT
    assert str(app.spin_btn.cget("state")) == "normal"
    assert str(app.new_game_btn.cget("state")) == "disabled"
    for row in app.slot_labels:
        for label in row:
            assert label.cget("text") == "?"


def test_new_game_clears_the_win_highlight(app, popups, monkeypatch):
    force_board(monkeypatch, TOP_ROW_WIN)
    set_inputs(app, 1, 1)
    app.spin()
    app.new_game()
    for row in app.slot_labels:
        for label in row:
            assert label.cget("bg") == slot_machine.COLOR_CREAM

def test_enter_key_spins(app, popups, monkeypatch):
    force_board(monkeypatch, NO_WIN)
    set_inputs(app, 1, 10)
    app._on_enter()
    assert app.balance == slot_machine.STARTING_BALANCE - 10


def test_enter_key_does_nothing_after_game_over(app, popups, monkeypatch):
    force_board(monkeypatch, NO_WIN)
    set_inputs(app, 1, 100)
    app.spin()
    popups.clear()
    app._on_enter()
    assert app.balance == 0
    assert popups == []