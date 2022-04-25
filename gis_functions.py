import rasterio as rio
import rasterio.mask as mask
import geopandas as gpd
import os


def clip_raster_to_geometry(
    clipname="Clip-",
    rasterdir="",
    rasterfile="",
    outdir="./",
    geom_df=None,
    nodata=0,
    outcrs="",
):

    ras_src = rio.open(os.path.join(rasterdir, rasterfile))
    # ras_img = ras_src.read()
    ras_crs = ras_src.crs
    # convert clip geometry to raster crs
    geom_df = geom_df.to_crs(ras_crs)
    # Clip raster
    out_image, out_transform = mask.mask(
        ras_src, [geom_df.iloc[0].geometry], crop=True, nodata=nodata
    )
    out_meta = ras_src.meta
    out_meta.update(
        {
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "nodata": nodata,
        }
    )
    with rio.open(outdir + clipname + rasterfile, "w", **out_meta) as dest:
        dest.write(out_image)
    return out_image


def clip_shp_to_geometry(
    clipname="Clip-", shpdir="", shpfile="", outdir="./", geom_df=None
):
    gdf = gpd.read_file(os.path.join(shpdir, shpfile))
    geom_crs = geom_df.crs
    # shpcrs = gdf.crs
    # geom_df = geom_df.to_crs(shpcrs)
    gdf = gdf.to_crs(geom_crs)
    gdf = gdf[gdf.within(geom_df.iloc[0].geometry)]
    gdf.to_file(os.path.join(outdir, clipname + shpfile))
    return gdf
