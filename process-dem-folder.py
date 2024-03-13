import os
import re
import sys
import string
import warnings
import multiprocessing
import pickle
from random import randint
import time
import argparse
from functools import partial

os.environ["USE_PYGEOS"] = "0"
import geopandas as gpd
import rasterio as rio
import rasterio.mask as mask
import rasterio.features
import rasterio.plot as riop
import py3dep
import rioxarray
import string
import glob

from gis_functions import clip_raster_to_geometry, clip_shp_to_geometry
from sinkhole_functions import calc_karst_fraction, get_carbs_only_huc


hucs_on_carbs_with_sinks = gpd.read_file("huc12_on_carbs_with_sinks.shp")
analysis_crs = "5070"
hucs_on_carbs_with_sinks.to_crs(analysis_crs, inplace=True)


def process_dem(dem_file, sinks="Combined"):
    print("Processing", dem_file)
    rasterdir = dem_file.split("/")[0]
    rasterfile = dem_file.split("/")[-1]
    huc12_str = dem_file.split("/")[-1].split("-")[0]
    # Grab geometry for this huc
    this_hu12 = hucs_on_carbs_with_sinks[
        hucs_on_carbs_with_sinks.huc12 == huc12_str
    ].geometry.values[0]

    imgsrc_elev = rio.open(dem_file)
    if not imgsrc_elev.crs == hucs_on_carbs_with_sinks.crs:
        print("CRS for dem and hucs dataframe do not match!")
        print("DEM:", imgsrc_elev.crs)
        print("DF:", hucs_on_carbs_with_sinks.crs)
        return -1

    if sinks == "USGS":
        sinks_dir = "./karst_depression_polys_conus/"
        sinks_file = "karst_depression_polys_conus.shp"
    elif sinks == "Mihevc":
        sinks_dir = "./us-dolines-mihevc"
        sinks_file = "merged-us-dolines.shp"
    elif sinks == "Combined":
        sinks_dir = "./combined-sinkholes"
        sinks_file = "combined-sinkholes-dissolved-5070.shp"
    else:
        print("Invalid sinkhole_dataset parameter value of:", sinks)
        raise ValueError

    full_sinks_path = os.path.join(sinks_dir, sinks_file)
    huc_mask = gpd.GeoSeries([this_hu12], crs=analysis_crs)
    huc_sinks = gpd.read_file(full_sinks_path, mask=huc_mask)
    sinks_shp = os.path.join(rasterdir, huc12_str + "-" + sinks + "-sinks.shp")
    # Check if sinks file exists
    # Fiona seems to fail if empty file exists, which can happen in failed runs.
    # To avoid this, we will remove any prior files.
    if os.path.isfile(sinks_shp):
        for f in glob.glob(sinks_shp[:-3] + "*"):
            os.remove(f)
    if huc_sinks.crs != imgsrc_elev.crs:
        huc_sinks = huc_sinks.to_crs(imgsrc_elev.crs)
    huc_sinks.to_file(sinks_shp)
    huc_sinks["ID"] = huc_sinks.index.values
    sinks_list = huc_sinks[["geometry", "ID"]].values.tolist()
    if len(sinks_list) == 0:
        # no sinks in basin
        rasterdir = os.path.abspath(rasterdir)
        carbs_only_huc = get_carbs_only_huc(
            huc_mask, datadir=rasterdir, demfile=rasterfile
        )
        return {"p_karst": 0.0, "carbs_huc": carbs_only_huc, "huc12": huc12_str}
    else:
        out_shape = imgsrc_elev.shape
        out_trans = imgsrc_elev.transform
        sinks_array = rasterio.features.rasterize(
            sinks_list, fill=0, out_shape=out_shape, transform=out_trans
        )
        profile = imgsrc_elev.profile
        sinks_raster = sinks_shp[:-3] + "tif"
        with rasterio.open(sinks_raster, "w", **profile) as dest:
            dest.write(sinks_array.astype(rasterio.int32), 1)

        rasterdir = os.path.abspath(rasterdir)
        sinksfile = os.path.abspath(os.path.join(".", sinks_raster))
        basefilename = huc12_str + "-" + sinks
        p_karst, carbs_only_huc = calc_karst_fraction(
            datadir=rasterdir,
            demfile=rasterfile,
            sinksfile=sinksfile,
            mean_filter=False,
            basefilename=basefilename,
            huc=huc_mask,
        )
        print(
            "HU",
            huc12_str,
            "has",
            str(p_karst)[:5],
            "percent internal karst drainage.",
        )
        return {"p_karst": p_karst, "carbs_huc": carbs_only_huc, "huc12": huc12_str}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-n",
        "--ncpus",
        help="number of processes to use for parallel processing (default 4)",
        default="4",
    )
    parser.add_argument(
        "-s",
        "--sinks",
        help="Which sinks shapefile to use (default=USGS).",
        choices=["USGS", "Mihevc", "Combined"],
        default="Combined",
    )
    args = parser.parse_args()
    n_processes = int(args.ncpus)
    sinks = args.sinks

    dem_files = [
        f
        for f in glob.glob("carb_huc_dems/*.tif")
        if re.search(r"[\d]{12}-3DEP.tif", f)
    ]

    with multiprocessing.Pool(processes=n_processes) as pool:
        process_dem_wopts = partial(process_dem, sinks=sinks)
        res = pool.map(process_dem_wopts, dem_files)

    for this_dict in res:
        huc12_str = this_dict["huc12"]
        wantidx = hucs_on_carbs_with_sinks.index[
            hucs_on_carbs_with_sinks.huc12 == huc12_str
        ]
        hucs_on_carbs_with_sinks.loc[wantidx, "p_karst"] = this_dict["p_karst"]
        hucs_on_carbs_with_sinks.loc[wantidx, "geometry"] = this_dict["carbs_huc"]

    hucs_on_carbs_with_sinks.to_file("carb_huc_dems/processed_hucs.shp")
