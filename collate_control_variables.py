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


def get_rock_types(huc):
    huc_geom = huc.geometry
    huc_area = huc_geom.area
    huc12 = huc.huc12
    huc_rocks = karst[karst.intersects(huc_geom)]
    this_huc_rocks_list = []
    for j, rock in huc_rocks.iterrows():
        rock_poly = rock.geometry.intersection(huc_geom)
        percent_area = rock_poly.area / huc_area
        this_huc_rocks_list.append(
            {
                "huc12": huc12,
                "rocktype1": rock.ROCKTYPE1,
                "rocktype2": rock.ROCKTYPE2,
                "percent_area": percent_area,
                "induration": rock.Induration,
                "exposure": rock.Exposure,
                "unit_name": rock.UNIT_NAME,
                "unit_age": rock.UNIT_AGE,
            }
        )
    return this_huc_rocks_list


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

with Pool(10) as p:
    huc_rocks_list = p.map(get_rock_types, [row for i, row in p_karst_df.iterrows()])

huc_rocks_list_flat = [x for xs in huc_rocks_list for x in xs]
huc_rocks_df = pd.DataFrame(huc_rocks_list_flat)
# Filter to only cases where one rock type fills more than half of the HUC
huc_rocks_df = huc_rocks_df[huc_rocks_df.percent_area > 0.5]
p_with_rocks = p_karst_df.merge(huc_rocks_df, on="huc12", how="left")

# Join rocks dataframe with other controls
different_cols = p_with_rocks.columns.difference(p_karst_df_with_controls.columns)
keep_cols = different_cols.append(pd.Index(["huc12"]))
p_karst_df_with_controls = p_karst_df_with_controls.merge(
    p_with_rocks[keep_cols], on="huc12", how="inner", copy=True
)

# Write out shapefile
p_karst_df_with_controls.to_file("p_karst_with_controls_5070.shp")