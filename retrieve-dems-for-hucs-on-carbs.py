import os
import geopandas as gpd
import py3dep

hucs_on_carbs_with_sinks = gpd.read_file("huc12_on_carbs_with_sinks.shp")

max_tries = 3
dem_res = 10

rasterdir = "carb_huc_dems"
if not os.path.exists(rasterdir):
    os.makedirs(rasterdir)

hucs_completed = []
hucs_failed = []

for idx, row in hucs_on_carbs_with_sinks.iterrows():
    huc12_str = row.huc12
    this_hu12 = row.geometry
    rasterfile = huc12_str + "-3DEP.tif"

    finished = False
    tries = 0

    full_rasterfile_path = os.path.join(rasterdir, rasterfile)

    # Check if we already have the dem
    if not os.path.isfile(full_rasterfile_path):
        while not finished:
            try:
                print("Downloading dem for ", huc12_str)
                dem = py3dep.get_dem(this_hu12, dem_res)
                finished = True
                failed = False
                # Convert to projected CRS
                dem = dem.rio.reproject(5070)
                dem.rio.to_raster(full_rasterfile_path)
                hucs_completed.append(huc12_str)
                print("this huc ", huc12_str)
            except Exception as error:
                print("Failed to retrieve DEM for", huc12_str + ".")
                print("error:", error)
                tries += 1
                if tries > max_tries:
                    finished = True
                    failed = True
                    hucs_failed.append(huc12_str)
        if failed:
            print(
                "Failed to retrieve the DEM (" + huc12_str + ") after",
                str(max_tries),
                "tries.",
            )
    else:
        print(
            "We already have dem raster",
            rasterfile,
            " continuing without download.",
        )

print(hucs_completed)

completed_file = os.path.join(rasterdir, "completed_dems.txt")
with open(completed_file, "w") as f:
    for huc in hucs_completed:
        f.write("%s\n" % huc)
print(hucs_completed)
failed_file = os.path.join(rasterdir, "failed_dems.txt")
with open(failed_file, "w") as f:
    for huc in hucs_failed:
        f.write("%s\n" % huc)
