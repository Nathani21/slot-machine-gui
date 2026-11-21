import io
import time
import tkinter as tk
import wave

import pytest

import slot_machine
from slot_machine import (
    COLS,
    ROWS,
    check_winnings,
    format_result,
    get_spin,
    load_high_score,
    save_high_score,
    symbol_count,
    symbol_value,
)

real_play_sound = slot_machine.play_sound

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
def app(tk_root, tmp_path):
    window = tk.Toplevel(tk_root)
    window.withdraw()
    yield slot_machine.SlotMachine(
        window, score_path=tmp_path / "highscore.json", animate=False
    )
    window.destroy()


@pytest.fixture
def animated_app(tk_root, tmp_path, monkeypatch):
    monkeypatch.setattr(slot_machine, "SPIN_FRAME_MS", 1)
    window = tk.Toplevel(tk_root)
    window.withdraw()
    yield slot_machine.SlotMachine(window, score_path=tmp_path / "highscore.json")
    window.destroy()


def wait_for_spin(tk_root, app, timeout=5.0):
    deadline = time.monotonic() + timeout
    while str(app.spin_btn.cget("state")) == "disabled" and time.monotonic() < deadline:
        tk_root.update()
        time.sleep(0.001)


@pytest.fixture(autouse=True)
def sounds(monkeypatch):
    played = []
    monkeypatch.setattr(slot_machine, "play_sound", played.append)
    return played


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

# High score
def test_load_high_score_missing_file_returns_starting_balance(tmp_path):
    assert load_high_score(tmp_path / "nope.json") == slot_machine.STARTING_BALANCE


def test_high_score_round_trip(tmp_path):
    path = tmp_path / "scores" / "highscore.json"
    save_high_score(path, 750)
    assert load_high_score(path) == 750


@pytest.mark.parametrize("content", ["not json", "[]", '{"high_score": "abc"}', "{}"])
def test_load_high_score_ignores_bad_files(tmp_path, content):
    path = tmp_path / "highscore.json"
    path.write_text(content)
    assert load_high_score(path) == slot_machine.STARTING_BALANCE


def test_new_best_balance_is_saved_and_shown(app, popups, monkeypatch, tmp_path):
    force_board(monkeypatch, TOP_ROW_WIN)
    set_inputs(app, 1, 10)
    app.spin()
    best = slot_machine.STARTING_BALANCE + symbol_value["A"] * 10 - 10
    assert app.high_score_label.cget("text") == f"Best: ${best}"
    assert load_high_score(tmp_path / "highscore.json") == best


def test_losing_does_not_lower_the_best(app, popups, monkeypatch):
    force_board(monkeypatch, NO_WIN)
    set_inputs(app, 1, 10)
    app.spin()
    assert app.high_score == slot_machine.STARTING_BALANCE


def test_saved_best_is_loaded_at_start(tk_root, tmp_path):
    path = tmp_path / "highscore.json"
    save_high_score(path, 900)
    window = tk.Toplevel(tk_root)
    window.withdraw()
    game = slot_machine.SlotMachine(window, score_path=path)
    assert game.high_score == 900
    assert game.high_score_label.cget("text") == "Best: $900"
    window.destroy()

# Spin animation
def test_spin_button_is_disabled_while_the_reels_spin(
    animated_app, tk_root, popups, monkeypatch
):
    force_board(monkeypatch, NO_WIN)
    set_inputs(animated_app, 1, 10)
    animated_app.spin()
    assert str(animated_app.spin_btn.cget("state")) == "disabled"
    assert animated_app.result_label.cget("text") == "Spinning..."
    animated_app._on_enter()  # ignored while spinning
    wait_for_spin(tk_root, animated_app)
    assert str(animated_app.spin_btn.cget("state")) == "normal"
    assert animated_app.balance == slot_machine.STARTING_BALANCE - 10


def test_animated_spin_ends_on_the_real_result(
    animated_app, tk_root, popups, monkeypatch
):
    force_board(monkeypatch, TOP_ROW_WIN)
    set_inputs(animated_app, 1, 10)
    animated_app.spin()
    wait_for_spin(tk_root, animated_app)
    win = symbol_value["A"] * 10
    assert [label.cget("text") for label in animated_app.slot_labels[0]] == ["A", "A", "A"]
    assert animated_app.balance == slot_machine.STARTING_BALANCE + win - 10
    for label in animated_app.slot_labels[0]:
        assert label.cget("bg") == slot_machine.COLOR_GOLD


def test_win_highlight_clears_as_the_next_spin_starts(
    animated_app, tk_root, popups, monkeypatch
):
    set_inputs(animated_app, 1, 1)
    force_board(monkeypatch, TOP_ROW_WIN)
    animated_app.spin()
    wait_for_spin(tk_root, animated_app)
    force_board(monkeypatch, NO_WIN)
    animated_app.spin()
    for row in animated_app.slot_labels:
        for label in row:
            assert label.cget("bg") == slot_machine.COLOR_CREAM
    wait_for_spin(tk_root, animated_app)

# Sound
class FakeWinsound:
    SND_MEMORY = 4

    def __init__(self):
        self.played = []

    def PlaySound(self, data, flags):
        self.played.append((data, flags))


def test_winning_spin_plays_the_win_sound(app, popups, sounds, monkeypatch):
    force_board(monkeypatch, TOP_ROW_WIN)
    set_inputs(app, 1, 10)
    app.spin()
    assert sounds == ["win"]


def test_losing_spin_plays_a_tick(app, popups, sounds, monkeypatch):
    force_board(monkeypatch, NO_WIN)
    set_inputs(app, 1, 10)
    app.spin()
    assert sounds == ["tick"]


def test_game_over_plays_only_the_game_over_sound(app, popups, sounds, monkeypatch):
    force_board(monkeypatch, NO_WIN)
    set_inputs(app, 1, 100)
    app.spin()
    assert sounds == ["game_over"]


def test_sound_switch_silences_everything(app, popups, sounds, monkeypatch):
    app.sound_on.set(False)
    force_board(monkeypatch, TOP_ROW_WIN)
    set_inputs(app, 1, 10)
    app.spin()
    assert sounds == []


def test_each_reel_stop_ticks_during_the_animation(
    animated_app, tk_root, popups, sounds, monkeypatch
):
    force_board(monkeypatch, NO_WIN)
    set_inputs(animated_app, 1, 10)
    animated_app.spin()
    wait_for_spin(tk_root, animated_app)
    assert sounds == ["tick", "tick", "tick"]


def test_play_sound_plays_the_wav_from_memory(monkeypatch):
    fake = FakeWinsound()
    monkeypatch.setattr(slot_machine, "winsound", fake)
    thread = real_play_sound("win")
    thread.join(timeout=2)
    assert fake.played == [(slot_machine.WAVES["win"], fake.SND_MEMORY)]


def test_make_wav_builds_a_valid_wav_of_the_right_length():
    data = slot_machine.make_wav([(440, 100)])
    with wave.open(io.BytesIO(data)) as wav:
        assert wav.getnchannels() == 1
        assert wav.getframerate() == slot_machine.SAMPLE_RATE
        assert wav.getnframes() == int(slot_machine.SAMPLE_RATE * 100 / 1000)


def test_play_sound_is_silent_without_winsound(monkeypatch):
    monkeypatch.setattr(slot_machine, "winsound", None)
    assert real_play_sound("win") is None