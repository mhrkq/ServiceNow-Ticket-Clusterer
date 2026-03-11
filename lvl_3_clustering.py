import pandas as pd
import time
from collections import Counter

from outlier_reassignment import run_outlier_reassignment

def run_lvl_3_clustering(start_time, df, X, input_file, log_callback=print):

    def log_message(message):
        elapsed_time = time.time() - start_time
        mins, secs = divmod(elapsed_time, 60)
        log_callback(f"[{int(mins)}m {int(secs)}s] [Lvl 3 Clustering] {message}")

    lvl2_names = df["Lvl 2 Cluster Name"].dropna()
    lvl2_names = lvl2_names[lvl2_names != ""].unique()

    name_to_words = {name: set(name.split()) for name in lvl2_names}

    visited = set()
    lvl3_clusters = []

    for name in sorted(lvl2_names):
        if name in visited:
            continue
        group = [name]
        visited.add(name)
        for other_name in lvl2_names:
            if other_name in visited:
                continue
            if len(name_to_words[name].intersection(name_to_words[other_name])) >= 1:
                group.append(other_name)
                visited.add(other_name)
        if len(group) > 1:
            lvl3_clusters.append(group)

    name_to_lvl3 = {}
    for i, group in enumerate(lvl3_clusters):
        for name in group:
            name_to_lvl3[name] = i

    lvl3_cluster_names = {}
    for i, group in enumerate(lvl3_clusters):
        all_words = [word for name in group for word in name_to_words[name]]
        most_common_words = [word for word, _ in Counter(all_words).most_common(3)]
        lvl3_cluster_names[i] = " ".join(most_common_words)

    df["Lvl 3 Cluster"] = df["Lvl 2 Cluster Name"].map(name_to_lvl3)
    df["Lvl 3 Cluster Name"] = df["Lvl 3 Cluster"].map(lvl3_cluster_names)

    df["Lvl 3 Cluster"] = df["Lvl 3 Cluster"].astype("Int64")  # Nullable int
    df["Lvl 3 Cluster Name"] = df["Lvl 3 Cluster Name"].fillna("")

    total_lvl2 = len(lvl2_names)
    unclustered_lvl2 = total_lvl2 - len(name_to_lvl3)
    log_message(f"Number of Lvl 3 Clusters formed: {len(lvl3_clusters)}")

    log_message("Names of Lvl 3 Clusters formed:")
    for i, name in lvl3_cluster_names.items():
        log_message(f"  [{i+1}] {name}")

    unclustered_names = [name for name in lvl2_names if name not in name_to_lvl3]
    log_message(f"{unclustered_lvl2}/{total_lvl2} Lvl 2 Clusters did not get grouped into a Lvl 3 Cluster")
    log_message("Names of ungrouped Lvl 2 Clusters:")
    for name in unclustered_names:
        log_message(f"  - {name}")

    total_points = len(df)
    lvl1_points = df["Lvl 1 Cluster Name"][(df["Cluster"] != -1) & (df["Lvl 1 Cluster Name"].notna())].count()
    lvl2_points = df["Lvl 2 Cluster Name"].str.strip().replace("", pd.NA).notna().sum()
    lvl3_points = df["Lvl 3 Cluster Name"].str.strip().replace("", pd.NA).notna().sum()

    log_message(f"Data coverage:")
    log_message(f"  Lvl 1 clustered: {lvl1_points}/{total_points}")
    log_message(f"  Lvl 2 clustered: {lvl2_points}/{total_points}")
    log_message(f"  Lvl 3 clustered: {lvl3_points}/{total_points}")

    log_message("Lvl 3 Clustering (Keyword Overlap) complete!")

    run_outlier_reassignment(start_time, df, X, input_file, log_callback)