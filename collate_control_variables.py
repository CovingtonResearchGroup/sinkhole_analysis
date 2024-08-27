import rasterio as rio
import os

os.environ["USE_PYGEOS"] = "0"
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from rasterstats import zonal_stats
import seaborn as sns
from scipy.stats import spearmanr, pearsonr
from multiprocessing import Pool
import os
import pickle
from functools import partial
from get_rock_types import get_rock_types


n_cpus = 8

if __name__ == "__main__":

    raster_key = pd.read_excel("raster-data-key.xlsx", index_col=0)

    p_karst_df = gpd.read_file("share/analysis-layers/processed_hucs.shp")
    # Raster data is in EPSG:4326
    p_karst_df_4326 = p_karst_df.to_crs("4326")

    def calc_raster_stats(parameter, raster_key=raster_key):
        raster_dir = raster_key["dir"][parameter]
        raster_filename = raster_key["filename"][parameter]
        full_raster_path = os.path.join(raster_dir, raster_filename)
        scale = raster_key["scale"][parameter]
        offset = raster_key["offset"][parameter]

        with rio.open(full_raster_path) as src:
            affine = src.transform
            nans = src.nodatavals[0]
            array = src.read(1)
            array = array.astype("float")
            array[array == nans] = np.nan
            if src.crs == 4326:
                df_zonal_stats = pd.DataFrame(
                    zonal_stats(p_karst_df_4326, array, affine=affine, all_touched=True)
                )

            else:
                # this_p_karst = p_karst_df
                df_zonal_stats = pd.DataFrame(
                    zonal_stats(
                        p_karst_df,
                        array,
                        affine=affine,
                        all_touched=True,
                    )
                )
            # df[parameter] = df_zonal_stats['mean'].values * scale + offset
            means = df_zonal_stats["mean"] * scale + offset

        return means

    # Process raster layers and add to p_karst dataframe
    means_dict = {}
    for param in raster_key.index:
        print("Processing " + param + "...")
        means_dict[param] = calc_raster_stats(param)

    means_df = pd.DataFrame(means_dict)
    p_karst_df_with_controls = p_karst_df.join(means_df)

    ### Get rock types from USGS karst map
    karst = gpd.read_file("USGS-Karst-Map/Carbonates48.shp")
    karst = karst.to_crs("5070")

    print("Getting rock types...")
    with Pool(n_cpus) as p:
        huc_rocks_list = p.map(
            partial(get_rock_types, karst=karst),
            [row for i, row in p_karst_df.iterrows()],
        )

    huc_rocks_list_flat = [x for xs in huc_rocks_list for x in xs]
    huc_rocks_df = pd.DataFrame(huc_rocks_list_flat)
    # Filter to only cases where rock type covers at least 10% of the HUC
    huc_rocks_df = huc_rocks_df[huc_rocks_df.percent_area > 0.1]

    # create boolean columns: True if a rocktype is a carbonate, False otherwise
    huc_rocks_df["rocktype1_is_carb"] = (
        (huc_rocks_df["rocktype1"] == "limestone")
        | (huc_rocks_df["rocktype1"] == "dolostone (dolomite)")
        | (huc_rocks_df["rocktype1"] == "carbonate")
        | (huc_rocks_df["rocktype1"] == "calcarenite")
    )
    huc_rocks_df["rocktype2_is_carb"] = (
        (huc_rocks_df["rocktype2"] == "limestone")
        | (huc_rocks_df["rocktype2"] == "dolostone (dolomite)")
        | (huc_rocks_df["rocktype2"] == "carbonate")
        | (huc_rocks_df["rocktype2"] == "calcarenite")
    )
    # Calculate exposure index
    is_exposed = huc_rocks_df["exposure"] == "E"
    is_B3 = huc_rocks_df["exposure"] == "B3"
    huc_rocks_df["exposure_index"] = is_exposed.astype(float)
    # Set cases with less than 50 feet of cover to 0.5
    huc_rocks_df["exposure_index"][is_B3] = 0.5

    # convert from true/false to 1/0 for carb_index math. Otherwise behavior is unpredictable
    huc_rocks_df["rocktype1_is_carb"] = huc_rocks_df["rocktype1_is_carb"].astype(float)
    huc_rocks_df["rocktype2_is_carb"] = huc_rocks_df["rocktype2_is_carb"].astype(float)

    # If huc is more than 50% one rocktype, record this rock type
    has_dominant_rocktype = huc_rocks_df["percent_area"] > 0.5
    huc_rocks_df["dominant_rocktype"] = (
        has_dominant_rocktype.astype(int) * huc_rocks_df["rocktype1"]
    )
    huc_rocks_df["dominant_rocktype"][~has_dominant_rocktype] = "None"

    # calculate carbonate index: index = (rocktype1_is_carb + rocktype2_is_carb) / N_recorded_rock_types
    huc_rocks_df["rocktype_carb_index"] = (
        huc_rocks_df["rocktype1_is_carb"] + huc_rocks_df["rocktype2_is_carb"]
    ) / 2
    huc_rocks_df["huc_carb_index"] = 0.0
    huc_rocks_df["huc_pct_area_represented_in_index"] = 0.0
    print("Calculating carbonate and exposure index for each HUC...")
    for huc12 in huc_rocks_df.huc12.unique():
        # record the percent of HUC area that was used in the calculation
        # (in other words, how much of the HUC is accounted for by rock units
        # above whatever area threshold we used)
        huc_rocks_df.loc[
            huc_rocks_df["huc12"] == huc12, "huc_pct_area_represented_in_index"
        ] = np.sum(huc_rocks_df.loc[huc_rocks_df["huc12"] == huc12, "percent_area"])
        # calculate and store the area-weighted carbonate index
        huc_rocks_df.loc[huc_rocks_df["huc12"] == huc12, "huc_carb_index"] = (
            np.sum(
                huc_rocks_df.loc[huc_rocks_df["huc12"] == huc12, "rocktype_carb_index"]
                * huc_rocks_df.loc[huc_rocks_df["huc12"] == huc12, "percent_area"]
            )
            / huc_rocks_df.loc[
                huc_rocks_df["huc12"] == huc12, "huc_pct_area_represented_in_index"
            ]
        )
        # calculate and store the area-weighted exposure index
        huc_rocks_df.loc[huc_rocks_df["huc12"] == huc12, "exposure_index"] = (
            np.sum(
                huc_rocks_df.loc[huc_rocks_df["huc12"] == huc12, "exposure_index"]
                * huc_rocks_df.loc[huc_rocks_df["huc12"] == huc12, "percent_area"]
            )
            / huc_rocks_df.loc[
                huc_rocks_df["huc12"] == huc12, "huc_pct_area_represented_in_index"
            ]
        )
        # Look for cases with dominant rocktype and copy to all rock sub-hucs for preservation
        # before decimation.
        dominant_rock = huc_rocks_df.loc[
            huc_rocks_df.huc12 == huc12, "dominant_rocktype"
        ][huc_rocks_df.loc[huc_rocks_df.huc12 == huc12, "dominant_rocktype"] != "None"]
        if len(dominant_rock) > 0:
            huc_rocks_df.loc[huc_rocks_df.huc12 == huc12, "dominant_rocktype"] = (
                dominant_rock.iloc[0]
            )

    # now create a decimated copy of huc_rocks_df so that there aren't
    # duplicate hucs when we join with the climate/soils/pkarst info
    huc_rocks_df_decimated = huc_rocks_df.drop_duplicates(
        subset=["huc12"], keep="first"
    )
    # remove rocktype info because there are mulptiple rock types per huc;
    # this can always be found in the non-decimated df but is misleading in the
    # decimated one because we deleted duplicate HUC lines which removed rock
    # type info
    huc_rocks_df_decimated = huc_rocks_df_decimated.drop(
        columns=[
            "rocktype1",
            "rocktype2",
            "percent_area",
            "induration",
            "exposure",
            "unit_name",
            "unit_age",
            "rocktype1_is_carb",
            "rocktype2_is_carb",
            "rocktype_carb_index",
        ]
    )

    p_with_rocks = p_karst_df.merge(huc_rocks_df_decimated, on="huc12", how="left")

    # Join rocks dataframe with other controls
    different_cols = p_with_rocks.columns.difference(p_karst_df_with_controls.columns)
    keep_cols = different_cols.append(pd.Index(["huc12"]))
    p_karst_df_with_controls = p_karst_df_with_controls.merge(
        p_with_rocks[keep_cols], on="huc12", how="inner", copy=True
    )

    # Merge slope information
    with open("huc_relief.pkl", "rb") as f:
        slopes_df = pickle.load(f)

    p_karst_df_with_controls = p_karst_df_with_controls.merge(
        slopes_df, on="huc12", how="inner", copy=True
    )

    # Write out shapefile
    p_karst_df_with_controls.to_file("temp_p_karst_with_controls_5070.shp")
