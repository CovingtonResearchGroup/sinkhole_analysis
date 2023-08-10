import os

os.environ["USE_PYGEOS"] = "0"
import geopandas as gpd
from karstification import calc_karstification_for_HU12
from pandas import read_excel
from pynhd import pynhd
import py3dep
from shapely import box
import os
import sys
import string
import warnings
import multiprocessing
import pickle
from random import randint
import time

hr = pynhd.NHDPlusHR("huc12")
huc12 = pynhd.WaterData("wbd12", crs="epsg:4326")
box_df = read_excel("bounding_boxes.xlsx")
bbox_zip = zip(box_df.x_min, box_df.y_min, box_df.x_max, box_df.y_max)
project_dir = "./qgis"


def format_filename(s):
    """Take a string and return a valid filename constructed from the string.
    Uses a whitelist approach: any characters not present in valid_chars are
    removed. Also spaces are replaced with underscores.

    Note: this method may produce invalid filenames such as ``, `.` or `..`
    When I use this method I prepend a date string like '2009_01_15_19_46_32_'
    and append a file extension like '.txt', so I avoid the potential of using
    an invalid filename.
    """
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = "".join(c for c in s if c in valid_chars)
    filename = filename.replace(" ", "_")  # I don't like spaces in filenames.
    return filename


def process_box(bbox_enum, overwrite=False):
    # Randomize query times to that they don't come at once
    sleeptime = randint(1, 10)
    time.sleep(sleeptime)
    p_karst_list = []
    i, bbox = bbox_enum
    boxname = box_df.Name[i]
    print("Processing", boxname)
    # Check if box csv already exists
    box_dirname = format_filename(boxname)
    box_path = os.path.join("./qgis/", box_dirname)
    csv_exists = False
    if not overwrite:
        if os.path.isfile(os.path.join(box_path, "bbox_df.csv")):
            csv_exists = True

    if overwrite or not csv_exists:
        box_hucs12 = huc12.bybox(bbox)
        # Check available resolution
        avail = py3dep.check_3dep_availability(bbox)
        if avail["3m"] == True:
            dem_res = 3
            found_res = True
        elif avail["5m"] == True:
            dem_res = 5
            found_res = True
        elif avail["10m"] == True:
            dem_res = 10
            found_res = True
        else:
            found_res = False
        if found_res:
            print("Using dem resolution", str(dem_res))
            box_poly = box(*bbox)
            box_gdf = gpd.GeoDataFrame(index=[0], crs="epsg:4326", geometry=[box_poly])
            if not os.path.exists(box_path):
                os.makedirs(box_path)

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                box_gdf.to_file(os.path.join(box_path, box_dirname + ".shp"))
                box_hucs12.to_file(os.path.join(box_path, "box_hucs.shp"))

            for hu_idx in box_hucs12.index:
                hu = box_hucs12.iloc[hu_idx]
                huc_num = hu.huc12
                print("HUC", huc_num)
                hu.crs = "EPSG:4326"
                p_karst = calc_karstification_for_HU12(
                    hu, boxname=box_dirname, dem_res=dem_res
                )
                p_karst_list.append(p_karst)

                print(
                    "HU",
                    huc_num,
                    "has",
                    str(p_karst)[:5],
                    "percent internal karst drainage.",
                )

        else:
            print("No dem available at required resolutions.")
            p_karst_list.append(-1)

        box_hucs12["p_karst"] = p_karst_list
        output_hucs_file = os.path.join(box_path, "bbox_df.csv")
        box_hucs12.to_csv(output_hucs_file)
        return box_hucs12
    else:
        print(boxname, "csv file already exists. Skipping.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        n_processes = int(sys.argv[1])
    else:
        n_processes = 4
    with multiprocessing.Pool(processes=n_processes) as pool:
        pool.map(process_box, enumerate(bbox_zip))
