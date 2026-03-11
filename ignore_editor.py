import tkinter as tk
from tkinter import simpledialog, messagebox
import os

def edit_ignore_words(file_path="ignore_words.txt"):
    def load_words():
        if not os.path.exists(file_path):
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            return sorted(set(w.strip() for w in f if w.strip()))

    def save_words(words):
        with open(file_path, "w", encoding="utf-8") as f:
            for word in sorted(set(words)):
                f.write(word + "\n")

    def refresh_listbox():
        listbox.delete(0, tk.END)
        for word in words:
            listbox.insert(tk.END, word)
        counter_label.config(text=f"Total Words: {len(words)}")

    def add_word():
        word = simpledialog.askstring("Add Ignore Word", "Enter word to ignore:")
        if word:
            word = word.strip().lower()
            if word and word not in words:
                words.append(word)
                refresh_listbox()
                save_words(words)

    def remove_selected():
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Select a word to remove.")
            return
        word = listbox.get(selection[0])
        words.remove(word)
        refresh_listbox()
        save_words(words)

    words = load_words()

    editor = tk.Toplevel()
    editor.title("Edit Ignore Words")
    editor.geometry("400x400")

    tk.Label(editor, text="Ignore Words:").pack(pady=5)
    listbox = tk.Listbox(editor, selectmode=tk.SINGLE, height=15, width=40)
    listbox.pack(padx=10, pady=10)

    counter_label = tk.Label(editor, text=f"Total Words: {len(words)}")
    counter_label.pack()

    button_frame = tk.Frame(editor)
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="Add Word", command=add_word).pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="Remove Selected", command=remove_selected).pack(side=tk.LEFT, padx=10)

    refresh_listbox()
    editor.mainloop()