import pandas as pd
import time

from c1_to_c3 import run_c1_to_c3

def run_outlier_reassignment(start_time, df, X, input_file, log_callback=print):

    def log_message(message):
        elapsed_time = time.time() - start_time
        mins, secs = divmod(elapsed_time, 60)
        log_callback(f"[{int(mins)}m {int(secs)}s] [Reassigning Outliers] {message}")

    outliers = df[df["Cluster"] == -1].copy()
    non_outliers = df[df["Cluster"] != -1].copy()

    initial_outlier_count = len(outliers)
    assigned_to_lvl2 = 0
    assigned_to_lvl3 = 0

    lvl2_name_to_words = {
        name: set(name.split()) for name in non_outliers["Lvl 2 Cluster Name"].dropna().unique()
        if isinstance(name, str) and name.strip()
    }

    lvl3_name_to_words = {
        name: set(name.split()) for name in non_outliers["Lvl 3 Cluster Name"].dropna().unique()
        if isinstance(name, str) and name.strip()
    }

    # Try to slot outliers
    for idx, row in outliers.iterrows():
        name = row["clean_text"]
        words = set(name.split())

        # Try Lvl 2 match (≥3 common words)
        matched = False
        for lvl2_name, lvl2_words in lvl2_name_to_words.items():
            if len(words & lvl2_words) >= 3:
                outliers.at[idx, "Lvl 2 Cluster Name"] = lvl2_name
                assigned_to_lvl2 += 1
                matched = True
                break

        # If no Lvl 2 match, try Lvl 3 match (≥1 common word)
        if not matched:
            for lvl3_name, lvl3_words in lvl3_name_to_words.items():
                if len(words & lvl3_words) >= 1:
                    outliers.at[idx, "Lvl 3 Cluster Name"] = lvl3_name
                    assigned_to_lvl3 += 1
                    matched = True
                    break

    final_df = pd.concat([non_outliers, outliers], ignore_index=True)

    clustered_outliers = assigned_to_lvl2 + assigned_to_lvl3
    final_outliers = initial_outlier_count - clustered_outliers
    lvl1_cluster_names = set(final_df["Lvl 1 Cluster Name"].dropna().unique())
    lvl1_cluster_names_mapped_to_lvl2 = set(
        final_df[final_df["Lvl 2 Cluster Name"].notna() & (final_df["Lvl 2 Cluster Name"] != "")]["Lvl 1 Cluster Name"].dropna().unique()
    )
    unclustered_lvl1_clusters = lvl1_cluster_names - lvl1_cluster_names_mapped_to_lvl2
    lvl2_cluster_names = set(final_df["Lvl 2 Cluster Name"].dropna().unique()) - {""}
    lvl2_cluster_names_mapped_to_lvl3 = set(
        final_df[final_df["Lvl 3 Cluster Name"].notna() & (final_df["Lvl 3 Cluster Name"] != "")]["Lvl 2 Cluster Name"].dropna().unique()
    )
    unclustered_lvl2_clusters = lvl2_cluster_names - lvl2_cluster_names_mapped_to_lvl3
    lvl3_cluster_names = set(final_df["Lvl 3 Cluster Name"].dropna().unique()) - {""}
    lvl3_cluster_count = len(lvl3_cluster_names)
    total_unclustered = len(unclustered_lvl1_clusters) + len(unclustered_lvl2_clusters) + lvl3_cluster_count

    log_message(f"{clustered_outliers}/{initial_outlier_count} outliers assigned to Lvl 2 or Lvl 3 clusters.")
    log_message(f"{assigned_to_lvl2} outliers assigned to Lvl 2 clusters.")
    log_message(f"{assigned_to_lvl3} outliers assigned to Lvl 3 clusters.")
    log_message(f"{final_outliers} outliers remain.")
    log_message(f"Unclustered Lvl 1 Clusters: {len(unclustered_lvl1_clusters)}")
    log_message(f"Unclustered Lvl 2 Clusters: {len(unclustered_lvl2_clusters)}")
    log_message(f"Number of Lvl 3 Clusters: {lvl3_cluster_count}")
    log_message(f"Sum of Unclustered Lvl 1, Lvl 2, and Lvl 3 Clusters: {total_unclustered}")

    log_message("Outlier reassignment complete!")

    run_c1_to_c3(start_time, df, X, input_file, final_df, lvl3_name_to_words, lvl1_cluster_names, lvl2_cluster_names, clustered_outliers, initial_outlier_count, assigned_to_lvl2, assigned_to_lvl3, final_outliers, log_callback, output_dir="output")