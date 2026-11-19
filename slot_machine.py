import random
import tkinter as tk
from tkinter import messagebox

# Constants
MAX_LINES, MAX_BET, MIN_BET, ROWS, COLS = 3, 100, 1, 3, 3
STARTING_BALANCE = 100

symbol_count = {
    "A": 2, "B": 4, "C": 6, "D": 8
}

symbol_value = {
    "A": 5, "B": 4, "C": 3, "D": 2
}

# LOGIC
def check_winnings(columns, lines, bet):
    winnings = 0
    winning_lines = []

    for line in range(lines):
        symbol = columns[0][line]
    
        for column in columns:
            if column[line] != symbol:
                break
        else:
            winnings += symbol_value[symbol] * bet
            winning_lines.append(line + 1)

    return winnings, winning_lines

def get_spin():
    all_symbols = []
    for symbol, count in symbol_count.items():
        all_symbols.extend([symbol] * count)
    
    columns = []
    for _ in range(COLS):
        column = []
        current = all_symbols[:]

        for _ in range(ROWS):
            val = random.choice(current)
            current.remove(val)
            column.append(val)
        
        columns.append(column)
    
    return columns

# GUI
class SlotMachine:
    def __init__(self, root):
        self.root = root
        self.root.title("Slot Machine")

        self.balance = STARTING_BALANCE

        self._build_balance_label()
        self._build_reels()
        self._build_inputs()
        self._build_buttons()

    def _build_balance_label(self):
        self.balance_label = tk.Label(
            self.root, text=f"Balance: ${self.balance}", font=("Arial", 14)
        )
        self.balance_label.pack(pady=10)

    def _build_reels(self):
        self.slot_labels = []
        for r in range(ROWS):
            row = []
            frame = tk.Frame(self.root)
            frame.pack()
            for c in range(COLS):
                lbl = tk.Label(frame, text="?", font=("Arial", 24), width=4)
                lbl.pack(side=tk.LEFT, padx=5, pady=5)
                row.append(lbl)
            self.slot_labels.append(row)

    def _build_inputs(self):
        tk.Label(self.root, text=f"Lines (1-{MAX_LINES})").pack()
        self.lines_entry = tk.Entry(self.root)
        self.lines_entry.insert(0, "1")
        self.lines_entry.pack(pady=5)

        tk.Label(self.root, text=f"Bet per line (${MIN_BET}-${MAX_BET})").pack()
        self.bet_entry = tk.Entry(self.root)
        self.bet_entry.insert(0, str(MIN_BET))
        self.bet_entry.pack(pady=5)

    def _build_buttons(self):
        self.spin_btn = tk.Button(
            self.root, text="SPIN", command=self.spin, bg="green", fg="white"
        )
        self.spin_btn.pack(pady=10)

        self.new_game_btn = tk.Button(
            self.root, text="NEW GAME", command=self.new_game, state=tk.DISABLED
        )
        self.new_game_btn.pack(pady=(0, 10))
    
    def spin(self):
        try:
            lines = int(self.lines_entry.get())
            bet = int(self.bet_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Enter whole numbers for lines and bet.")
            return

        if not (1 <= lines <= MAX_LINES):
            messagebox.showerror("Error", f"Lines must be between 1 and {MAX_LINES}.")
            return

        if not (MIN_BET <= bet <= MAX_BET):
            messagebox.showerror("Error", f"Bet must be between {MIN_BET} and {MAX_BET}.")
            return

        total_bet = lines * bet

        if total_bet > self.balance:
            messagebox.showerror("Error", "Not enough balance!")
            return

        slots = get_spin()

        # Display slots
        for r in range(ROWS):
            for c in range(COLS):
                self.slot_labels[r][c].config(text=slots[c][r])

        winnings, win_lines = check_winnings(slots, lines, bet)

        self.balance += winnings - total_bet

        self.balance_label.config(text=f"Balance: ${self.balance}")

        messagebox.showinfo(
            "Result", f"You won ${winnings}\nWinning lines: {win_lines}"
        )

        if self.balance < MIN_BET:
            self.game_over()

    def game_over(self):
        self.spin_btn.config(state=tk.DISABLED)
        self.new_game_btn.config(state=tk.NORMAL)
        messagebox.showinfo(
            "Game over", "You're out of money! Click NEW GAME to play again."
        )

    def new_game(self):
        self.balance = STARTING_BALANCE
        self.balance_label.config(text=f"Balance: ${self.balance}")
        for row in self.slot_labels:
            for label in row:
                label.config(text="?")
        self.spin_btn.config(state=tk.NORMAL)
        self.new_game_btn.config(state=tk.DISABLED)

# Run app
if __name__ == "__main__":
    root = tk.Tk()
    app = SlotMachine(root)
    root.mainloop()