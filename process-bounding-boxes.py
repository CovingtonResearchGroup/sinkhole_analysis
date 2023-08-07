import geopandas as gpd
from karstification import calc_karstification_for_HU12
from pandas import read_excel
from pynhd import pynhd
from shapely import box
import os
import string
import warnings

hr = pynhd.NHDPlusHR("huc12")
huc12 = pynhd.WaterData("wbd12", crs="epsg:4326")


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


box_df = read_excel("bounding_boxes.xlsx")
bbox_zip = zip(box_df.x_min, box_df.y_min, box_df.x_max, box_df.y_max)

hucs_list = []
p_karst_list = []

for i, bbox in enumerate(bbox_zip):
    if i > 1:
        print(asdf)
    boxname = box_df.Name[i]
    print("Processing", boxname)
    box_hucs12 = huc12.bybox(bbox)
    box_poly = box(*bbox)
    box_gdf = gpd.GeoDataFrame(index=[0], crs="epsg:4326", geometry=[box_poly])
    box_dirname = format_filename(boxname)
    box_path = os.path.join("./qgis/", box_dirname)
    if not os.path.exists(box_path):
        os.makedirs(box_path)
    box_gdf.to_file(os.path.join(box_path, box_dirname + ".shp"))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        box_hucs12.to_file(os.path.join(box_path, "box_hucs.shp"))

    for hu_idx in box_hucs12.index:
        hu = box_hucs12.iloc[hu_idx]
        huc_num = hu.huc12
        print("HUC", huc_num)
        hu.crs = "EPSG:4326"
        p_karst = calc_karstification_for_HU12(hu, boxname=box_dirname)
        hucs_list.append(huc_num)
        p_karst_list.append(p_karst)

        print(
            "HU", huc_num, "has", str(p_karst)[:5], "percent internal karst drainage."
        )
