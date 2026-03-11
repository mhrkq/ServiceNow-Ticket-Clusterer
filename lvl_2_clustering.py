import time
from collections import Counter

from lvl_3_clustering import run_lvl_3_clustering

def run_lvl_2_clustering(start_time, df, X, input_file, log_callback=print):

    def log_message(message):
        elapsed_time = time.time() - start_time
        mins, secs = divmod(elapsed_time, 60)
        log_callback(f"[{int(mins)}m {int(secs)}s] [Lvl 2 Clustering] {message}")

    level_1_cluster_ids = df.loc[df["Cluster"] != -1, "Cluster"].unique()
    log_message(f"Number of Lvl 1 Cluster IDs: {len(level_1_cluster_ids)}")

    log_message("Merging clusters with duplicate Lvl 1 Cluster Names...")

    name_to_clusters = df[df["Cluster"] != -1].groupby("Lvl 1 Cluster Name")["Cluster"].unique()

    duplicates_before_merge = {name: clusters.tolist() for name, clusters in name_to_clusters.items() if len(clusters) > 1}
    log_message(f"Number of duplicate Lvl 1 Cluster Names before merge: {len(duplicates_before_merge)}")

    if duplicates_before_merge:
        log_message("Duplicated Lvl 1 Cluster Names and their associated Cluster IDs:")
        for i, (name, clusters) in enumerate(duplicates_before_merge.items(), 1):
            log_message(f"[{i}] {name}: Cluster IDs = {clusters}")

    cluster_merge_map = {}
    for name, cluster_ids in name_to_clusters.items():
        primary_id = cluster_ids[0]
        for cid in cluster_ids:
            cluster_merge_map[cid] = primary_id

    df.loc[df["Cluster"] != -1, "Cluster"] = df.loc[df["Cluster"] != -1, "Cluster"].map(cluster_merge_map)
    log_message("Cluster ID remapping complete.")

    lvl1_names = df.loc[df["Cluster"] != -1, "Lvl 1 Cluster Name"].dropna().unique()
    log_message(f"Number of Lvl 1 Cluster Names: {len(lvl1_names)}")
    lvl1_cluster_ids = df.loc[df["Cluster"] != -1, "Cluster"].unique()
    cluster_to_name = df.loc[df["Cluster"] != -1, ["Cluster", "Lvl 1 Cluster Name"]].dropna().drop_duplicates()
    named_cluster_ids = set(cluster_to_name["Cluster"])
    missing_cluster_ids = set(lvl1_cluster_ids) - named_cluster_ids
    log_message(f"Number of Lvl 1 Clusters: {len(lvl1_cluster_ids)}")
    log_message(f"Number of Named Lvl 1 Clusters: {len(named_cluster_ids)}")
    log_message(f"Lvl 1 Clusters without names: {len(missing_cluster_ids)}")
    if missing_cluster_ids:
        log_message("Clusters missing Lvl 1 names:")
        for idx, cid in enumerate(sorted(missing_cluster_ids), 1):
            log_message(f"[{idx}] Cluster ID: {cid}")

    name_counts = df.loc[df["Cluster"] != -1].groupby("Lvl 1 Cluster Name")["Cluster"].nunique()
    reused_names = name_counts[name_counts > 1]
    log_message(f"Number of reused Lvl 1 names: {len(reused_names)}")

    name_to_words = {name: set(name.split()) for name in lvl1_names}

    visited = set()
    lvl2_clusters = []

    for name in lvl1_names:
        if name in visited:
            continue
        group = [name]
        visited.add(name)
        for other_name in lvl1_names:
            if other_name in visited:
                continue
            if len(name_to_words[name].intersection(name_to_words[other_name])) >= 3:
                group.append(other_name)
                visited.add(other_name)
        if len(group) > 1:
            lvl2_clusters.append(group)

    name_to_lvl2 = {}
    for i, group in enumerate(lvl2_clusters):
        for name in group:
            name_to_lvl2[name] = i

    lvl2_cluster_names = {}
    for i, group in enumerate(lvl2_clusters):
        all_words = [word for name in group for word in name_to_words[name]]
        most_common_words = [word for word, _ in Counter(all_words).most_common(3)]
        lvl2_cluster_names[i] = " ".join(most_common_words)

    df["Lvl 2 Cluster"] = df["Lvl 1 Cluster Name"].map(name_to_lvl2)
    df["Lvl 2 Cluster Name"] = df["Lvl 2 Cluster"].map(lvl2_cluster_names)

    df["Lvl 2 Cluster"] = df["Lvl 2 Cluster"].astype("Int64")  # Nullable integer
    df["Lvl 2 Cluster Name"] = df["Lvl 2 Cluster Name"].fillna("")

    total_lvl1 = len(named_cluster_ids)
    unclustered_lvl1 = total_lvl1 - len(name_to_lvl2)
    log_message(f"{unclustered_lvl1}/{total_lvl1} Lvl 1 Clusters did not get grouped into a Lvl 2 Cluster")
    log_message(f"Number of Lvl 2 Clusters formed: {len(lvl2_clusters)}")

    log_message("Lvl 2 Clustering (Keyword Overlap) complete!")

    run_lvl_3_clustering(start_time, df, X, input_file, log_callback)