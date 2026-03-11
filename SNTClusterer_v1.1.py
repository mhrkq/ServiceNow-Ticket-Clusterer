# terminal command to create application folder:
# pyinstaller --noconfirm --onedir --windowed `
# >>   --add-data "model/all-distilroberta-v1;model/all-distilroberta-v1" `
# >>   SNTClusterer_v1.1.py
# >>
#
# creates a folder containing "-internal" folder and ServiceNowTicketClusterer app

import tkinter as tk

def launch_gui():
    splash_root = tk.Tk()
    splash_root.overrideredirect(True)
    splash_root.geometry("300x100+500+300")
    tk.Label(splash_root, text="Starting SNTClusterer...", font=("Arial", 12)).pack(expand=True)
    splash_root.update()
    # splash_root.after(100, lambda: splash_root.update())  # Keeps it responsive

    from tkinter import filedialog, scrolledtext, messagebox
    import threading
    import os
    import ctypes
    import shutil
    from encoding import run_encoding
    from ignore_editor import edit_ignore_words
    from help_page import help_page

    OUTPUT_DIR = "output"
    IGNORE_WORDS_PATH = "ignore_words.txt"
    HELP_PATH = "help.txt"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    extra_ignore_words = {
        "message", "attachments", "recipient", "additional", 
        "comments", "detailed", "description", "ticket", 
        "issue", "user", "work", "notes", 
        "cc", "subject", "sent", "number",
        "hi", "team", "email", "information",
        "confidential", "privileged", "protected", "law",
        "distributed", "used", "copied", "authorisation",
        "pm", "yes", "yesno", "said",
        "wed", "jan", "users", "case",
        "thank", "thanks", "solarwinds", "cloudsek",
        "cybersecopsinternationalsoscom", "cyber", "operations", "security",
        "dlglbitoinfosecoperations", "anomaly", "detected", "nan"
    }

    if not os.path.exists(IGNORE_WORDS_PATH):
        with open(IGNORE_WORDS_PATH, "w") as f:
            for word in sorted(extra_ignore_words):
                f.write(word + "\n")

    help_lines = [
        "Clustering Steps:",
        "1. Use 'Short description', 'Description', 'Comments and Work notes', 'Configuration Item', ",
        "   and 'Impacted Location' sections of ServiceNow ticket.",
        "2. Remove names from 'Assigned to' section and custom list of ignore words from text data, ",
        "   which do not value-add to the clustering process.",
        "3. Cluster tickets into Level 1 Cluster using DistilRoBERTa model.",
        "4. Name them using TF-IDF method (keyword frequency).",
        "   - NOTE: Cluster names (5 keywords) are top 5 most common keywords in the cluster.",
        "5. Cluster the Level 1 Clusters into Level 2 Clusters.",
        "   - Cluster all level 1 clusters with at least 3 same keywords.",
        "6. Cluster the Level 2 Clusters into Level 3 Clusters.",
        "   - Cluster all level 2 clusters with at least 1 same keyword.",
        "7. Reassign outliers into either Level 2 or Level 3 clusters.",
        "   - First, try to reassign outlier into level 1 cluster (at least 3 same keywords).",
        "   - Second, try to reassign outlier into level 2 cluster (at least 1 same keyword).",
        "8. Slot Level 1 Clusters with no parents (unclustered) into Level 3 Clusters.",
        "   - Cluster all level 1 clusters with at least 1 same keyword as level 3 cluster.",
        "",
        "Clustering Progress:",
        "1. For each ticket, data from 'Short description', 'Description', 'Comments and Work notes', ",
        "   'Configuration Item', and 'Impacted Location' sections are consolidated.",
        "2. Agent names, special characters, numbers, and words from custom ignore list are removed.",
        "3. Tickets are grouped into Level 1 Clusters.",
        "   - Tickets that cannot be clustered are labelled as 'Outliers'.",
        "4. Level 1 Clusters are named, with each name consisting of 5 keywords.",
        "5. Level 1 Clusters are grouped into Level 2 Clusters (3 keywords).",
        "6. Level 2 Clusters are grouped into Level 3 Clusters (3 keywords), even if clustered based on ",
        "   only 1 shared keyword.",
        "7. Outliers are reassigned to Level 2 or 3 Clusters.",
        "   - Outliers that cannot be reassigned remain as outliers.",
        "8. Unclustered Level 1 Clusters are grouped into Level 3 Clusters.",
        "   - Level 1 Clusters that cannot be grouped remain as standalone clusters.",
        "",
        "Clustering Result:",
        "Net Clusters = Unclustered Level 1 Clusters + Unclustered Level 2 Clusters + Level 3 Clusters",
        "Total Dataset = Net Clusters + Remaining Outliers",
        "",
        "Supported File Types:",
        "csv, xlsx, xlsm, xltm",
        "",
        "Version:",
        "1.1",
        "",
        "Notes:",
        "This clustering tool is created for computers with low specifications, without GPU capabilities.",
        "The tool uses DistilRoBERTa, a smaller, faster version of the RoBERTa language model.",
        "DistilRoBERTa keeps most of its accuracy while being more efficient to run.",
        "The first round of clustering is the most accurate but creates many clusters.",
        "Having an input of tens of thousands of tickets will likely result in hundreds of clusters.",
        "Thus, to make the output more meaningful, a second and third round of grouping are done.",
        "This tool is designed to be able to cluster inputs ranging from hundreds to tens of ",
        "thousands of tickets.",
        "The bulk of the run time is spent on encoding.",
    ]

    if not os.path.exists(HELP_PATH):
        with open(HELP_PATH, "w") as f:
            for line in help_lines:
                f.write(line + "\n")

    # to_hide = ["help.txt", "ignore_words.txt", "output", "_internal"]
    to_hide = ["_internal"]
    for item in to_hide:
        if os.path.exists(item):
            ctypes.windll.kernel32.SetFileAttributesW(item, 0x02)  # 0x02 = Hidden attribute

    selected_file_path = None

    stop_spinner = threading.Event()

    def choose_file():
        global selected_file_path
        path = filedialog.askopenfilename(
            filetypes=[
                ("Supported files", "*.xlsx *.csv *.xltm *.xlsm"),
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("Macro-enabled Excel files", "*.xlsm"),
                ("Excel Template files", "*.xltm"),
                ("All files", "*.*")
            ]
        )
        if path:
            selected_file_path = path
            # file_label.config(text=f"Selected File: {os.path.basename(path)}")
            set_file_label(f"Selected File: {os.path.basename(path)}")
            log_area.insert(tk.END, f"📁 File selected: {path}\n")
            log_area.see(tk.END)
            btn_run.config(state=tk.NORMAL)
            status_label.config(text="Status: Idle", fg="gray")

    def start_spinner():
        spinner_states = ["Running", "Running.", "Running..", "Running..."]
        spinner_index = 0
        def spin():
            nonlocal spinner_index
            if not stop_spinner.is_set():
                status_label.config(text=spinner_states[spinner_index % len(spinner_states)], fg="blue")
                spinner_index += 1
                root.after(500, spin)
        spin()

    def start_pipeline_thread():
        global selected_file_path
        if not selected_file_path:
            messagebox.showwarning("No file", "Please choose a file first.")
            return

        log_area.delete(1.0, tk.END)
        btn_run.config(state=tk.DISABLED)
        stop_spinner.clear()
        start_spinner()

        def logger(message):
            log_area.insert(tk.END, message + "\n")
            log_area.see(tk.END)

        def run():
            try:
                output_path = run_encoding(selected_file_path, log_callback=logger)
                logger(f"\n✅ Full Cluster complete!")
                stop_spinner.set()
                status_label.config(text="Status: Completed ✅", fg="green")
                refresh_file_list()
            except Exception as e:
                logger(f"\n❌ Error: {e}")
                stop_spinner.set()
                messagebox.showerror("Error", str(e))
                status_label.config(text="Status: Error ❌", fg="red")
            finally:
                btn_run.config(state=tk.NORMAL)

        threading.Thread(target=run, daemon=True).start()

    def refresh_file_list():
        file_listbox.delete(0, tk.END)
        has_files = False
        allowed_extensions = [".csv", ".xlsx", ".xlsm", ".xltm"]
        if os.path.exists(OUTPUT_DIR):
            for file in os.listdir(OUTPUT_DIR):
                if os.path.splitext(file)[1].lower() in allowed_extensions:
                    file_listbox.insert(tk.END, file)
                    has_files = True
        clear_btn.config(state=tk.NORMAL if has_files else tk.DISABLED)

    def set_file_label(path, max_chars=40):
        display_text = path if len(path) <= max_chars else path[:max_chars - 3] + "..."
        file_label.config(text=display_text)

    def download_selected_file():
        selection = file_listbox.curselection()
        if not selection:
            messagebox.showinfo("No selection", "Please select a file from the list.")
            return
        file_name = file_listbox.get(selection[0])
        src_path = os.path.join(OUTPUT_DIR, file_name)
        ext = os.path.splitext(file_name)[1] or ".xlsx"
        dest_path = filedialog.asksaveasfilename(defaultextension=ext, initialfile=file_name, filetypes=[
            ("All Supported", "*.csv *.xlsx *.xlsm *.xltm"),
            ("CSV Files", "*.csv"),
            ("Excel Files", "*.xlsx"),
            ("Macro-enabled Excel", "*.xlsm"),
            ("Excel Template", "*.xltm"),
            ("All Files", "*.*")
        ])
        if dest_path:
            try:
                shutil.copy(src_path, dest_path)
                messagebox.showinfo("Success", f"File saved to:\n{dest_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file:\n{e}")

    def clear_output_files():
        if not os.path.exists(OUTPUT_DIR):
            messagebox.showinfo("No output folder", "Output folder does not exist.")
            return
        confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete all output files?")
        if confirm:
            try:
                for file in os.listdir(OUTPUT_DIR):
                    file_path = os.path.join(OUTPUT_DIR, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                messagebox.showinfo("Success", "All output files deleted.")
                refresh_file_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete files:\n{e}")

    def open_ignore_editor():
        edit_ignore_words(IGNORE_WORDS_PATH)

    def open_help_page():
        help_page(HELP_PATH)

    def on_closing():
        if os.path.exists(IGNORE_WORDS_PATH):
            try:
                os.remove(IGNORE_WORDS_PATH)
                print(f"{IGNORE_WORDS_PATH} deleted successfully.")
            except Exception as e:
                print(f"Error deleting {IGNORE_WORDS_PATH}: {e}")
        
        root.destroy()

    splash_root.destroy()

    root = tk.Tk()
    root.title("ServiceNow Ticket Clustering Tool v1.1")
    root.geometry("800x520")

    top_frame = tk.Frame(root)
    top_frame.pack(pady=5, fill=tk.X)

    btn_choose = tk.Button(top_frame, text="Choose File", command=choose_file, width=18)
    btn_choose.pack(side=tk.LEFT, padx=(50, 10))

    btn_run = tk.Button(top_frame, text="Run Clustering", command=start_pipeline_thread, state=tk.DISABLED, width=18)
    btn_run.pack(side=tk.LEFT, padx=(20, 0))

    info_frame = tk.Frame(top_frame)
    info_frame.pack(side=tk.LEFT, padx=20, fill=tk.X, expand=True)

    file_status_row = tk.Frame(info_frame)
    file_status_row.pack(anchor="w")

    file_label = tk.Label(file_status_row, text="No file selected", fg="blue", anchor="w")
    file_label.pack(side=tk.LEFT)

    status_label = tk.Label(file_status_row, text="Status: Idle", fg="gray", font=("Arial", 10, "bold"), anchor="w", padx=10)
    status_label.pack(side=tk.LEFT, padx=10)

    mid_button_frame = tk.Frame(root)
    mid_button_frame.pack(pady=(0, 0))

    btn_ignore_words = tk.Button(mid_button_frame, text="Manage Ignore Words", command=open_ignore_editor, width=18)
    btn_ignore_words.pack(side=tk.LEFT, padx=(0, 10))

    btn_help_page = tk.Button(mid_button_frame, text="Help", command=open_help_page, width=9)
    btn_help_page.pack(side=tk.LEFT)

    log_area = scrolledtext.ScrolledText(root, width=90, height=15)
    log_area.pack(padx=10, pady=5)

    download_frame = tk.Frame(root)
    download_frame.pack(pady=5)

    tk.Label(download_frame, text="Available Output Files:").pack()

    listbox_frame = tk.Frame(download_frame)
    listbox_frame.pack(pady=5)

    scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
    file_listbox = tk.Listbox(listbox_frame, width=60, height=4, yscrollcommand=scrollbar.set)
    scrollbar.config(command=file_listbox.yview)

    file_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    download_btn = tk.Button(download_frame, text="Download Selected File", command=download_selected_file, width=20)
    download_btn.pack()

    clear_btn = tk.Button(download_frame, text="Delete All Output Files", command=clear_output_files, fg="red", state=tk.DISABLED, width=20)
    clear_btn.pack(pady=(5, 0))

    refresh_file_list() # Load file list on start

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()  # Required for PyInstaller + multiprocessing on Windows
    launch_gui()