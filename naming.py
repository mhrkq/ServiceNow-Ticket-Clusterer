import time
import re
from sklearn.feature_extraction.text import TfidfVectorizer

from lvl_2_clustering import run_lvl_2_clustering

def run_naming(start_time, df, X, input_file, log_callback=print):

    def log_message(message):
        elapsed_time = time.time() - start_time
        mins, secs = divmod(elapsed_time, 60)
        log_callback(f"[{int(mins)}m {int(secs)}s] [Naming] {message}")

    if "clean_text" not in df.columns or "Cluster" not in df.columns:
        raise ValueError("Missing required columns: 'clean_text' and 'Cluster'")

    log_message("Grouping text by cluster...")
    cluster_texts = df[df["Cluster"] != -1].groupby("Cluster")["clean_text"].apply(lambda x: " ".join(x))
    log_message("Text grouped by cluster.")

    log_message("Applying TF-IDF...")
    tfidf = TfidfVectorizer(stop_words='english', max_features=1000)
    tfidf_matrix = tfidf.fit_transform(cluster_texts)
    feature_names = tfidf.get_feature_names_out()
    log_message("TF-IDF applied successfully.")

    def get_top_words(tfidf_matrix, feature_names, n=5):
        top_words = []
        for row in tfidf_matrix:
            indices = row.toarray().argsort()[0][-n * 2:][::-1]
            words = [feature_names[i] for i in indices if not re.search(r'\d', feature_names[i])]
            top_words.append(words[:n])
        return top_words

    log_message("Extracting top words for each cluster...")
    top_words_per_cluster = get_top_words(tfidf_matrix, feature_names)
    log_message("Top words extracted.")

    df["Lvl 1 Cluster Name"] = df["Cluster"].map(lambda x: "" if x == -1 else dict(zip(cluster_texts.index, [" ".join(words) for words in top_words_per_cluster])).get(x, "Unknown"))
    log_message("Cluster names generated using TF-IDF.")

    log_message("TF-IDF naming complete!")

    run_lvl_2_clustering(start_time, df, X, input_file, log_callback)