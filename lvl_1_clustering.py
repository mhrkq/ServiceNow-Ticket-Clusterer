
import time
import hdbscan
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

from naming import run_naming

def run_lvl1_clustering(start_time, df, X, input_file, X_reduced, log_callback=print):

    def log_message(message):
        elapsed_time = time.time() - start_time
        mins, secs = divmod(elapsed_time, 60)
        log_callback(f"[{int(mins)}m {int(secs)}s] [Lvl 1 Clustering] {message}")

    log_message("Starting HDBSCAN...")
    clusterer = hdbscan.HDBSCAN(min_cluster_size=2, min_samples=27, core_dist_n_jobs=1)
    df["Cluster"] = clusterer.fit_predict(X_reduced)
    log_message("HDBSCAN clustering completed.")

    num_clusters = len(set(df["Cluster"])) - (1 if -1 in df["Cluster"].values else 0)
    outlier_percentage = (sum(df["Cluster"] == -1) / len(df)) * 100
    log_message(f"Number of clusters formed: {num_clusters}")
    log_message(f"Percentage of outliers: {outlier_percentage:.2f}%")

    valid_clusters = df[df["Cluster"] != -1]
    if len(valid_clusters) > 1:
        silhouette = silhouette_score(X_reduced[valid_clusters.index], valid_clusters["Cluster"])
        db_index = davies_bouldin_score(X_reduced[valid_clusters.index], valid_clusters["Cluster"])
        ch_score = calinski_harabasz_score(X_reduced[valid_clusters.index], valid_clusters["Cluster"])

        log_message("min_cluster_size=2, min_samples=27")
        log_message(f"Silhouette Score: {silhouette:.4f}")
        log_message(f"Davies-Bouldin Index: {db_index:.4f}")
        log_message(f"Calinski-Harabasz Score: {ch_score:.4f}")
    else:
        log_message("Not enough valid clusters for clustering quality metrics.")

    log_message("Level 1 clustering complete!")

    run_naming(start_time, df, X, input_file, log_callback)