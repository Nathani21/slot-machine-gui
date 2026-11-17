import random
import tkinter as tk
from tkinter import messagebox

# Constants
MAX_LINES, MAX_BET, MIN_BET, ROWS, COLS = 3, 100, 1, 3, 3

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
            winnings += symbol_value[symbol] + bet
    
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

        self.balance = 100 # starting money

        # Balance Label
        self.balance_label = tk.Label(root, text=f"Balance: ${self.balance}", font=("Arial", 14))
        self.balance_label.pack(pady=10)

        # SLot Display
        self.slot_labels = []
        for r in range(ROWS):
            row = []
            frame = tk.Frame(root)
            frame.pack()
            for c in range(COLS):
                lbl = tk.Label(frame, text="?", font=("Arial", 24), width=4)
                lbl.pack(side=tk.LEFT, padx=5, pady=5)
                row.append(lbl)
            self.slot_labels.append(row)

        # Inputs
        self.lines_entry = tk.Entry(root)
        self.lines_entry.insert(0, "Lines (1-3)")
        self.lines_entry.pack(pady=5)

        self.bet_entry = tk.Entry(root)
        self.bet_entry.insert(0, "Bet per line")
        self.bet_entry.pack(pady=5)

        # Spin Button
        self.spin_btn = tk.Button(root, text="SPIN", command=self.spin, bg="green", fg="white")
        self.spin_btn.pack(pady=10)
    
    def spin(self):
        try:
            lines = int(self.lines_entry.get())
            bet = int(self.bet_entry.get())

            if not (1 <= lines <= MAX_LINES):
                raise ValueError("Invalid lines")
            
            if not (MIN_BET <= bet <= MAX_BET):
                raise ValueError("Invalid bet")
            
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
            
        except:
                messagebox.showerror("Error", "Enter valid numbers!")

# Run app
if __name__ == "__main__":
    root = tk.Tk()
    app = SlotMachine(root)
    root.mainloop()