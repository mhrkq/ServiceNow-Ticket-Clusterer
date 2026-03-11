import os
import pandas as pd
import time
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

from find_top_10_clusters import run_find_top_10_clusters

def run_c1_to_c3(start_time, df, X, input_file, final_df, lvl3_name_to_words, lvl1_cluster_names, lvl2_cluster_names, clustered_outliers, initial_outlier_count, assigned_to_lvl2, assigned_to_lvl3, final_outliers, log_callback=print, output_dir="output"):

    def log_message(message):
        elapsed_time = time.time() - start_time
        mins, secs = divmod(elapsed_time, 60)
        log_callback(f"[{int(mins)}m {int(secs)}s] [Slotting Lvl 1 into Lvl 3] {message}")

    assigned_lvl1_to_lvl3 = 0

    # Get Lvl 1 Cluster Names that are not already part of any Lvl 2 or Lvl 3
    unclustered_lvl1_df = final_df[
        (final_df["Lvl 2 Cluster Name"].isna() | (final_df["Lvl 2 Cluster Name"] == "")) &
        (final_df["Lvl 3 Cluster Name"].isna() | (final_df["Lvl 3 Cluster Name"] == ""))
    ]

    lvl1_name_to_words = {
        name: set(name.split()) for name in unclustered_lvl1_df["Lvl 1 Cluster Name"].dropna().unique()
        if isinstance(name, str) and name.strip()
    }

    # Use same lvl3_name_to_words mapping from earlier
    for lvl1_name, lvl1_words in lvl1_name_to_words.items():
        for lvl3_name, lvl3_words in lvl3_name_to_words.items():
            if len(lvl1_words & lvl3_words) >= 1:
                final_df.loc[final_df["Lvl 1 Cluster Name"] == lvl1_name, "Lvl 3 Cluster Name"] = lvl3_name
                assigned_lvl1_to_lvl3 += 1
                break  # Only assign to one Lvl 3 cluster

    lvl1_cluster_names_mapped_to_lvl2_or_lvl3 = set(
        final_df[
            (final_df["Lvl 2 Cluster Name"].notna() & (final_df["Lvl 2 Cluster Name"] != "")) |
            (final_df["Lvl 3 Cluster Name"].notna() & (final_df["Lvl 3 Cluster Name"] != ""))
        ]["Lvl 1 Cluster Name"].dropna().unique()
    )
    unclustered_lvl1_clusters = lvl1_cluster_names - lvl1_cluster_names_mapped_to_lvl2_or_lvl3

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
    log_message(f"(New) Lvl 1 Clusters assigned to Lvl 3 Clusters: {assigned_lvl1_to_lvl3}")

    input_basename, input_ext = os.path.splitext(os.path.basename(input_file))
    output_filename = f"{input_basename}_clustered{input_ext}"
    c1toc3_output_file = os.path.join(output_dir, output_filename)
    if input_ext.lower() in [".xlsx", ".xlsm", ".xltm"]:
        final_df.to_excel(c1toc3_output_file, index=False)
    elif input_ext.lower() == ".csv":
        final_df.to_csv(c1toc3_output_file, index=False)
    else:
        raise ValueError(f"Unsupported file format: {input_ext}")
    log_message("Cluster 1 slotting into Cluster 3 complete! Results saved.")

    # Coherence Score Calculation
    embeddings = X

    def compute_semantic_coherence(df, cluster_col, embeddings):
        cluster_embeddings = {}
        for idx, row in df.iterrows():
            cluster_id = row[cluster_col]
            if pd.isna(cluster_id) or cluster_id == "":
                continue
            cluster_embeddings.setdefault(cluster_id, []).append(embeddings[idx])

        coherence_scores = []
        for emb_list in tqdm(cluster_embeddings.values(), desc=f"Computing coherence for {cluster_col}"):
            if len(emb_list) < 2:
                continue
            sim_matrix = cosine_similarity(emb_list)
            upper_tri_indices = np.triu_indices_from(sim_matrix, k=1)
            pairwise_sims = sim_matrix[upper_tri_indices]
            coherence_scores.append(np.mean(pairwise_sims))

        overall_score = np.mean(coherence_scores) if coherence_scores else 0
        return overall_score

    lvl2_score = compute_semantic_coherence(df, "Lvl 2 Cluster Name", embeddings)
    lvl3_score = compute_semantic_coherence(df, "Lvl 3 Cluster Name", embeddings)

    log_message(f"Level 2 Clusters Coherence score: {lvl2_score}")
    log_message(f"Level 3 Clusters Coherence score: {lvl3_score}")
    log_message("Coherence score calculations complete!")

    run_find_top_10_clusters(start_time, input_basename, final_df, unclustered_lvl1_clusters, unclustered_lvl2_clusters, lvl3_cluster_names, input_ext, log_callback, output_dir="output")