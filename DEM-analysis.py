import richdem as rd
import numpy as np
import glob
import os
import pandas as pd
import pickle
from multiprocessing import Pool

dem_dir = "./carb_huc_dems/"  # "./zero_p_test/"

dem_tifs = glob.glob(os.path.join(dem_dir, "*3DEP.tif"))


def determine_median_slope(tif):
    huc_str = os.path.split(tif)[-1].split("-")[0]
    print("Processing " + huc_str)
    dem = rd.LoadGDAL(tif)
    slope = rd.TerrainAttribute(dem, attrib="slope_riserun")
    median_slope = np.median(slope[~np.isnan(slope)]).tolist()
    return (huc_str, median_slope)
    # slope_dict[huc_str] = np.median(slope[~np.isnan(slope)]).tolist()


with Pool(30) as p:
    huc_slope_list = p.map(determine_median_slope, dem_tifs)

slope_dict = {}
for huc in huc_slope_list:
    slope_dict[huc[0]] = huc[1]

slope_series = pd.Series(slope_dict)
with open("huc_slopes.pkl", "wb") as f:
    pickle.dump(slope_series, f)
