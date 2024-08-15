import richdem as rd
import numpy as np
import glob
import os
import pandas as pd
import pickle
from multiprocessing import Pool

# dem_dir = "./carb_huc_dems/"  # "./zero_p_test/"
dem_dir = "./zero_p_test/"

dem_tifs = glob.glob(os.path.join(dem_dir, "*3DEP.tif"))


def determine_median_slope(tif):
    huc_str = os.path.split(tif)[-1].split("-")[0]
    print("Processing " + huc_str)
    dem = rd.LoadGDAL(tif)
    slope = rd.TerrainAttribute(dem, attrib="slope_riserun")
    median_slope = np.median(slope[~np.isnan(slope)]).tolist()
    dem_no_nans = dem[~np.isnan(dem)]
    max_elev = dem_no_nans.max()
    min_elev = dem_no_nans.min()
    thresh_slope = np.tan(np.deg2rad(20))
    n_high_slope = len(slope[slope >= thresh_slope])
    n_low_slope = len(slope[slope < thresh_slope])
    f_steep = n_high_slope / (n_high_slope + n_low_slope)
    return (huc_str, median_slope, max_elev, min_elev, f_steep)
    # slope_dict[huc_str] = np.median(slope[~np.isnan(slope)]).tolist()


with Pool(10, maxtasksperchild=5) as p:
    huc_slope_list = p.map(determine_median_slope, dem_tifs)

relief_list = []
relief_dict = {}
for huc in huc_slope_list:
    relief_dict["huc12"] = huc[0]
    relief_dict["median_slope"] = huc[1]
    relief_dict["max_elev"] = huc[2]
    relief_dict["min_elev"] = huc[3]
    relief_dict["f_steep"] = huc[4]
    relief_list.append(relief_dict)


slope_df = pd.DataFrame.from_dict(relief_list)
with open("huc_relief.pkl", "wb") as f:
    pickle.dump(slope_df, f)
