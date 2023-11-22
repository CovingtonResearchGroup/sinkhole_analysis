import rasterio as rio
from whitebox.whitebox_tools import WhiteboxTools
import geopandas as gpd

import os

wbt = WhiteboxTools()


def rasterize_sinks_shp(shpfile, outfile, basefile):
    wbt.vector_polygons_to_raster(shpfile, outfile, base=basefile)


def calc_karst_fraction(
    datadir,
    demfile,
    sinksfile=None,
    fill_pits=True,
    mean_filter=True,
    basefilename=None,
    huc=None,
):
    if basefilename is None:
        basefilename = demfile.split(".")[0]
    datadir = os.path.abspath(datadir)
    sinksfile = os.path.abspath(sinksfile)
    # Define filenames
    dempath = os.path.join(datadir, demfile)
    pitfill_dempath = os.path.join(datadir, demfile[:-4] + "-pitfill.tif")
    smoothed_dempath = os.path.join(datadir, demfile[:-4] + "-smoothed.tif")
    sinkspath = os.path.join(datadir, demfile[:-4] + "-sinks.tif")
    d8path = os.path.join(datadir, demfile[:-4] + "-d8.tif")
    watershedspath = os.path.join(datadir, basefilename + "-catchments.tif")

    if mean_filter:
        # Smooth dem
        wbt.mean_filter(dempath, smoothed_dempath, 5, 5)
    else:
        smoothed_dempath = dempath

    if fill_pits:
        # Fill single-cell pits
        wbt.fill_single_cell_pits(smoothed_dempath, pitfill_dempath)
    else:
        pitfill_dempath = smoothed_dempath

    # Find sinks
    if sinksfile is None:
        wbt.sink(pitfill_dempath, sinkspath, zero_background=True)
    elif ".tif" in sinksfile:
        # Use available sinks file
        sinkspath = sinksfile
    elif ".shp" in sinksfile:
        # We have a shapefile, need to rasterize
        sinkspath = os.path.join(datadir, sinksfile.split(".")[0] + ".tif")
        rasterize_sinks_shp(sinksfile, sinkspath, dempath)

    # Calculate d8 flow direction
    wbt.d8_pointer(pitfill_dempath, d8path)
    # Find watersheds of sinks
    wbt.watershed(d8path, sinkspath, watershedspath)
    wat_src = rio.open(watershedspath)
    dem_src = rio.open(dempath)
    ndv = dem_src.nodata
    if huc is not None:
        huc_geom = huc.geometry
        huc_carbs = gpd.read_file(
            "./USGS-Karst-Map/Dissolved_carbonates_seperate_polys_E_B3.shp",
            mask=huc_geom,
        )
        if len(huc_carbs) > 0:
            carbs_dissolved = huc_carbs.dissolve()
            carbs_only_huc = huc_geom.intersection(carbs_dissolved.iloc[0].geometry)
            wat_elev, wat_out_transform = rio.mask.mask(
                dem_src, [carbs_only_huc], crop=True
            )
            wat, wat_elev_out_transform = rio.mask.mask(
                wat_src, [carbs_only_huc], crop=True
            )
            carbs_only_df = gpd.GeoDataFrame(
                {"geometry": [carbs_only_huc]}, crs=huc.crs
            )
            carbs_only_file = os.path.join(
                datadir, demfile.split("-")[0] + "-carbs_only_huc.shp"
            )
            carbs_only_df.to_file(carbs_only_file)
        else:
            return 0
    else:
        wat_elev = dem_src.read()
        wat = wat_src.read()
    nkarst = len(wat[wat > 0])
    ntotal = len(wat_elev[wat_elev != ndv])
    # nfluvial = len(wat[wat < 0])
    nfluvial = ntotal - nkarst
    print("n karst draining pixels =", nkarst)
    print("n fluvial draining pixels =", nfluvial)
    p_karst = nkarst / (nkarst + nfluvial)
    print("percent karst =", p_karst)
    return p_karst, carbs_only_huc
