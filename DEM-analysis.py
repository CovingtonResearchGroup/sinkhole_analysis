import richdem as rd
import numpy as np
import glob
import os
import pandas as pd
import pickle

dem_dir = "./carb_huc_dems/"

dem_tifs = glob.glob(os.path.join(dem_dir, "*3DEP.tif"))


slope_dict = []
for tif in dem_tifs:
    huc_str = os.path.split(tif).split("-")[0]
    print("Processing " + huc_str)
    dem = rd.LoadGDAL(tif)
    slope = rd.TerrainAttribute(dem, attrib="slope_riserun")
    slope_dict[huc_str] = np.median(slope[~np.isnan(slope)]).tolist()

slope_series = pd.Series(slope_dict)
with open("huc_slopes.pkl", "wb") as f:
    pickle.dump(slope_series, f)
