import geopandas as gpd
import rasterio as rio
import rasterio.mask as mask
import rasterio.features
import rasterio.plot as riop
import py3dep
import rioxarray
import string
import glob

import os
from gis_functions import clip_raster_to_geometry, clip_shp_to_geometry
from sinkhole_functions import calc_karst_fraction


def calc_karstification_for_HU12(
    HU12,
    sinkhole_dataset="USGS",
    dem_res=3,
    project_dir="./qgis",
    boxname="",
    max_tries=10,
    use_avail_dems=True,
):
    """
    Download HU12 DEM and calculate karst index.

    Parameters
    ----------
    HU12 : pandas Series - A huc object from pynhd WaterData.

    sinkhole_dataset : string - The name of the sinkhole dataset to use.
                        Options are USGS or Mihevc.

    Returns
    -------
    float : ki - Karstification index
    """

    huc12_str = HU12.huc12
    rasterdir = os.path.join(project_dir, boxname, huc12_str)
    if not os.path.exists(rasterdir):
        os.makedirs(rasterdir)
    rasterfile = huc12_str + "-3DEP.tif"

    this_hu12 = HU12.geometry
    finished = False
    tries = 0

    full_rasterfile_path = os.path.join(rasterdir, rasterfile)

    # Check if we already have the dem
    if not os.path.isfile(full_rasterfile_path) or not use_avail_dems:
        while not finished:
            try:
                dem = py3dep.get_map("DEM", this_hu12, resolution=dem_res)
                finished = True
                failed = False
            except Exception as error:
                print("Failed to retrieve DEM for", huc12_str + ".")
                print("error:", error)
                tries += 1
                if tries > max_tries:
                    finished = True
                    failed = True
        if failed:
            print("Failed to retrieve the DEM after", str(max_tries), "tries.")
            return -1

        dem.rio.to_raster(full_rasterfile_path)
    else:
        print("We already have dem raster", rasterfile, " continuing without download.")

    imgsrc_elev = rio.open(full_rasterfile_path)

    if sinkhole_dataset == "USGS":
        sinks_dir = "./karst_depression_polys_conus/"
        sinks_file = "karst_depression_polys_conus.shp"
        # polytag = "karst_depression_polys_conus"
    elif sinkhole_dataset == "Mihevc":
        sinks_dir = "./us-dolines-mihevc"
        sinks_file = "merged-us-dolines.shp"
        # polytag = ""
    else:
        print("Invalid sinkhole_dataset parameter value of:", sinkhole_dataset)
        raise ValueError

    full_sinks_path = os.path.join(sinks_dir, sinks_file)
    huc_mask = gpd.GeoSeries([HU12.geometry], crs=HU12.crs)
    huc_sinks = gpd.read_file(full_sinks_path, mask=huc_mask)
    sinks_shp = os.path.join(
        rasterdir, huc12_str + "-" + sinkhole_dataset + "-sinks.shp"
    )
    # Check if sinks file exists
    # Fiona seems to fail if empty file exists, which can happen in failed runs.
    # To avoid this, we will remove any prior files.
    if os.path.isfile(sinks_shp):
        for f in glob.glob(sinks_shp[:-3] + "*"):
            os.remove(f)
    huc_sinks.to_file(sinks_shp)
    huc_sinks["ID"] = huc_sinks.index.values
    sinks_list = huc_sinks[["geometry", "ID"]].values.tolist()
    if len(sinks_list) == 0:
        # no sinks in basin
        return 0.0
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
        basefilename = huc12_str + "-" + sinkhole_dataset
        p_karst = calc_karst_fraction(
            datadir=rasterdir,
            demfile=rasterfile,
            sinksfile=sinksfile,
            mean_filter=False,
            basefilename=basefilename,
        )
        return p_karst
