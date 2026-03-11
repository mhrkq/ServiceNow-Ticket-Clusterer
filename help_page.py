import tkinter as tk
import os

def help_page(file_path="help.txt"):
    def load_lines():
        if not os.path.exists(file_path):
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.rstrip("\n") for line in f]

    lines = load_lines()

    help_page = tk.Toplevel()
    help_page.title("Help Page")
    help_page.geometry("800x400")

    tk.Label(help_page, text="Help Contents:").pack(pady=5)

    frame = tk.Frame(help_page)
    frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    linebox = tk.Listbox(
        frame,
        selectmode=tk.SINGLE,
        height=30,
        width=100,
        font=("Courier", 10),
        yscrollcommand=scrollbar.set
    )
    linebox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar.config(command=linebox.yview)

    for line in lines:
        linebox.insert(tk.END, line)

    help_page.mainloop()