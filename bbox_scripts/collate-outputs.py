import glob
import pandas as pd
import os
import argparse

def delete_bbox_csvs(sinks_dataset):
    csvs = glob.glob("./qgis/**/"+sinks_dataset+"-bbox_df.csv", recursive=True)
    for csv in csvs:
        os.remove(csv)


def concat_csvs(sinks_dataset):
    # Define the directory path
    output_dir = "qgis"

    # Use glob to find all the files called 'USGS-bbox_df.csv' recursively
    box_csvs = glob.glob(
        output_dir + "/**/" + sinks_dataset + "-bbox_df.csv", recursive=True
    )

    box_dfs = []

    # Iterate through each CSV file path
    for csvfile in box_csvs:
        # Get the parent directory name
        box_name = os.path.basename(os.path.dirname(csvfile))
        box_df = pd.read_csv(csvfile, dtype={"huc12": str})
        box_df["box"] = box_name
        box_dfs.append(box_df)

    box_df_concat = pd.concat(box_dfs)

    box_df_concat = box_df_concat.set_index("huc12")
    # Remove duplicates
    box_df_concat = box_df_concat.drop_duplicates()

    # Output concatenated df
    box_df_concat.to_csv(sinks_dataset + "-concat.csv")




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sinks_dataset",
        help="Specify the sinkhole dataset.",
        choices=["USGS", "Mihevc", "Combined"],
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete all corresponding csv files.")
    args = parser.parse_args()
    clean = args.clean
    sinks_dataset = args.sinks_dataset
    if clean:
        ans = input("Are you sure you want to delete all csv files for "+sinks_dataset+"? (y/n)")
        if ans == 'y':
            delete_bbox_csvs(sinks_dataset)
    else:
        concat_csvs(sinks_dataset)
