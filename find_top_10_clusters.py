import os
import pandas as pd
import time

def run_find_top_10_clusters(start_time, input_basename, final_df, unclustered_lvl1_clusters, unclustered_lvl2_clusters, lvl3_cluster_names, input_ext, log_callback=print, output_dir="output"):

    def log_message(message):
        elapsed_time = time.time() - start_time
        mins, secs = divmod(elapsed_time, 60)
        log_callback(f"[{int(mins)}m {int(secs)}s] {message}")

    valid_lvl1 = final_df["Lvl 1 Cluster Name"].notna() & (final_df["Lvl 1 Cluster Name"] != "")
    valid_lvl2 = final_df["Lvl 2 Cluster Name"].notna() & (final_df["Lvl 2 Cluster Name"] != "")
    valid_lvl3 = final_df["Lvl 3 Cluster Name"].notna() & (final_df["Lvl 3 Cluster Name"] != "")

    lvl1_cluster_counts = final_df[valid_lvl1 & final_df["Lvl 1 Cluster Name"].isin(unclustered_lvl1_clusters)]["Lvl 1 Cluster Name"].value_counts()

    lvl2_cluster_counts = final_df[valid_lvl2 & final_df["Lvl 2 Cluster Name"].isin(unclustered_lvl2_clusters)]["Lvl 2 Cluster Name"].value_counts()

    lvl3_cluster_counts = final_df[valid_lvl3 & final_df["Lvl 3 Cluster Name"].isin(lvl3_cluster_names)]["Lvl 3 Cluster Name"].value_counts()

    combined_counts = pd.concat([lvl1_cluster_counts, lvl2_cluster_counts, lvl3_cluster_counts])

    top_10_clusters = combined_counts.sort_values(ascending=False).head(10)

    top_clusters_data = []

    log_message("Top 10 P2 to P4 ServiceNow ticket clusters:")

    for i, (name, count) in enumerate(top_10_clusters.items(), start=1):
        if name in unclustered_lvl1_clusters:
            level = "Lvl 1"
        elif name in unclustered_lvl2_clusters:
            level = "Lvl 2"
        elif name in lvl3_cluster_names:
            level = "Lvl 3"
        else:
            level = "Unknown"

        log_message(f"[{i}] {name} ({level}): {count} tickets")

        top_clusters_data.append({
            "Rank": i,
            "Cluster Name": name,
            "Cluster Level": level,
            "Ticket Count": count
        })

    top_clusters_df = pd.DataFrame(top_clusters_data)
    top10_ext = input_ext if input_ext.lower() in [".csv", ".xlsx", ".xlsm", ".xltm"] else ".xlsx"
    top10_filename = f"{input_basename}_top_10_largest_clusters{top10_ext}"
    top10_output_file = os.path.join(output_dir, top10_filename)

    if top10_ext.lower() == ".csv":
        top_clusters_df.to_csv(top10_output_file, index=False)
    else:
        top_clusters_df.to_excel(top10_output_file, index=False)

    log_message("Top 10 P2 to P4 ServiceNow ticket clusters found! Results saved.")