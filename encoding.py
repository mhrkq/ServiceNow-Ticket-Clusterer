import os
import sys
import pandas as pd
import time
import nltk
import string
from nltk.corpus import stopwords
import umap
import numpy as np
from sentence_transformers import SentenceTransformer

from lvl_1_clustering import run_lvl1_clustering

def run_encoding(input_file, log_callback=print):
    start_time = time.time()

    def log_message(message):
        elapsed_time = time.time() - start_time
        mins, secs = divmod(elapsed_time, 60)
        log_callback(f"[{int(mins)}m {int(secs)}s] [Encoding] {message}")

    log_message(f"Input file: {input_file}.")

    nltk.download('stopwords')
    stop_words = set(stopwords.words('english'))
    translator = str.maketrans("", "", string.punctuation)
    log_message("Stopwords downloaded and loaded.")

    file_ext = os.path.splitext(input_file)[1].lower()

    if file_ext == ".csv":
        try:
            df = pd.read_csv(input_file, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(input_file, encoding="windows-1252")
        log_message("CSV file loaded successfully.")
    elif file_ext in [".xlsx", ".xlsm", ".xltm"]:
        sheets = pd.read_excel(input_file, sheet_name=None, engine="openpyxl")
        df = pd.concat(sheets.values(), ignore_index=True)
        log_message("Excel file loaded and sheets combined.")
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")
    log_message("File loaded successfully.")

    expected_columns = [
        "Short description",
        "Description",
        "Configuration item"
    ]

    col_map = {col.lower(): col for col in df.columns}
    df_columns_lower = set(df.columns.str.lower())

    interchangeable_groups = [
        ("Location", "Impacted Location"),
        ("Comments and Work notes", "Work notes")
    ]

    missing_columns = [col for col in expected_columns if col.lower() not in col_map]

    for col1, col2 in interchangeable_groups:
        if col1.lower() not in df_columns_lower and col2.lower() not in df_columns_lower:
            missing_columns.append(f"{col1} / {col2}")

    if missing_columns:
        log_message(f"WARNING: Missing columns: {', '.join(missing_columns)}")


    def combine_text(row):
        return ' '.join(
            str(row.get(col_map.get(col.lower(), ''), ''))
            for col in expected_columns
        )

    df["text_data"] = df.apply(combine_text, axis=1)
    log_message("Text fields combined case-insensitively into 'text_data'.")

    assigned_names = set()

    for col in ["Assigned to", "Closed by"]:
        if col in df.columns:
            for name in df[col].dropna().unique():
                tokens = str(name).lower().split()
                assigned_names.update(tokens)
    log_message("Assigned-to and Closed-by names, if available, extracted.")

    def get_resource_path(relative_path):
        if getattr(sys, 'frozen', False):
            return os.path.join(os.path.dirname(sys.executable), relative_path)
        else:
            return os.path.join(os.path.abspath("."), relative_path)

    def load_ignore_words():
        file_path = get_resource_path("ignore_words.txt")
        if not os.path.exists(file_path):
            return set()
        with open(file_path, "r", encoding="utf-8") as f:
            return set(line.strip().lower() for line in f if line.strip())

    extra_ignore_words = load_ignore_words()
    ignore_words = assigned_names.union(extra_ignore_words)

    def clean_text(text):
        text = str(text).lower().translate(translator)
        return " ".join(
            word for word in text.split()
            if word not in stop_words and word not in ignore_words
        )

    df["clean_text"] = df["text_data"].apply(clean_text)
    log_message("Text data cleaned.")

    # model = SentenceTransformer('sentence-transformers/all-distilroberta-v1')
    if getattr(sys, 'frozen', False):
        current_dir = os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(__file__)
    script_model_path = os.path.join(current_dir, 'model', 'all-distilroberta-v1')
    app_model_path = os.path.join(current_dir, '_internal', 'model', 'all-distilroberta-v1')
    model_path = script_model_path if os.path.exists(script_model_path) else app_model_path
    model = SentenceTransformer(model_path)
    log_message("DistilRoBERTa model loaded.")
    log_message("Encoding using DistilRoBERTa...")

    # def encode_texts(texts, model, batch_size=1000):
    # def encode_texts(texts, model, batch_size=512):
    def encode_texts(texts, model, batch_size=256):
        return np.vstack(model.encode(texts, convert_to_numpy=True, batch_size=batch_size, show_progress_bar=False))

    X = encode_texts(df["clean_text"].tolist(), model)
    log_message("Text data encoded using DistilRoBERTa.")

    # umap_reducer = UMAP(n_components=50, random_state=42)
    # X_reduced = umap_reducer.fit_transform(X)
    # log_message("UMAP dimensionality reduction completed.")
    umap_model = umap.UMAP(
        n_neighbors=15,
        n_components=5,
        metric='cosine',
        random_state=42,
        low_memory=True,
        n_jobs=1
    )

    log_message("Starting UMAP reduction...")
    try:
        X_reduced = umap_model.fit_transform(X)
        log_message("UMAP reduction completed.")
    except Exception as e:
        log_message(f"❌ UMAP failed: {e}")

    run_lvl1_clustering(start_time, df, X, input_file, X_reduced, log_callback)

