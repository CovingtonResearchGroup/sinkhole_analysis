from osgeo import gdal
import rasterio as rio
from rasterio import features
import matplotlib.pyplot as plt
import os
import fiona

os.environ["USE_PYGEOS"] = "0"
import geopandas as gpd
import multiprocessing
import glob
import argparse
from osgeo_utils.ogrmerge import process as ogr_merge


def polygonize_catchment_tif(tif_file):
    print("Polygonizing", tif_file)
    src = rio.open(tif_file)
    img = src.read(1)
    mask = img > 0

    results = (
        {"properties": {"raster_val": v}, "geometry": s}
        for i, (s, v) in enumerate(
            features.shapes(img, mask=mask, transform=src.transform)
        )
    )

    shp_file = tif_file[:-3] + "shp"
    with fiona.open(
        shp_file,
        "w",
        driver="ESRI Shapefile",
        crs=src.crs.to_wkt(),
        schema={"properties": [("raster_val", "int")], "geometry": "Polygon"},
    ) as dst:
        dst.writerecords(results)


def merge_catchment_shps(catchment_dir):
    merged_gpkg = os.path.join(catchment_dir, "merged_catchments.gpkg")
    input_shps = os.path.join(catchment_dir, "*catchments.shp")
    ogr_merge(["-single", "-f", "GPKG", "-o", merged_gpkg, input_shps])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-n",
        "--ncpus",
        help="number of processes to use for parallel processing (default 4)",
        default="4",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="If flag is set, then all resulting shapefiles will be merged.",
    )

    parser.add_argument(
        "-d",
        "--dir",
        help="Directory containing catchment tifs.",
        default="./carb_huc_dems/catchments",
    )
    args = parser.parse_args()
    n_processes = int(args.ncpus)
    # overwrite = args.overwrite
    catchment_dir = args.dir

    catchment_tifs = glob.glob(os.path.join(catchment_dir, "*catchments.tif"))
    print(catchment_tifs)
    with multiprocessing.Pool(processes=n_processes) as pool:
        pool.map(polygonize_catchment_tif, catchment_tifs)

    if args.merge:
        merge_catchment_shps(catchment_dir)
