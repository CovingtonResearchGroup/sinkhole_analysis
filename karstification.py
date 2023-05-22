import geopandas as gpd 
import rasterio as rio 
import rasterio.mask as mask
import rasterio.features
import rasterio.plot as riop 
import py3dep
import rioxarray


import os
from gis_functions import clip_raster_to_geometry, clip_shp_to_geometry
from sinkhole_functions import calc_karst_fraction



def calc_karstification_for_HU10(HU10, sinkhole_dataset='USGS'):
    """
    Download HU10 DEM and calculate karst index.

    Parameters
    ----------
    HU10 : string - The number of the HU10 to run.

    sinkhole_dataset : string - The name of the sinkhole dataset to use. 
                        Options are USGS or Mihevc.
    
    Returns
    -------
    float : ki - Karstification index
    """

    #HU4 = HU10[:4]
    rasterdir = './NHD-data/'
    huc10_str = HU10.iloc[0].huc10
    rasterfile = huc10_str + '.tif'

    #hu10_geom = HU10.geometry #gpd.read_file('NHD-data/NHDPLUS_H_' + HU4 + '_HU4_GDB.gdb', layer='WBDHU10')
    this_hu10 = HU10.geometry # hu10[hu10.HUC10 == HU10]
    dem = py3dep.get_map("DEM", this_hu10.iloc[0], resolution=30)#, geo_crs="epsg:4326", crs="epsg:3857")
    dem.rio.to_raster(os.path.join(rasterdir, rasterfile))

    #img_elev = clip_raster_to_geometry(rasterdir=rasterdir,
    #                                    rasterfile=rasterfile,
    #                                    geom_df=this_hu10,
    #                                    clipname='HUC-' + huc10_str +'-')
    
    imgsrc_elev = rio.open(os.path.join(rasterdir, rasterfile))

    if sinkhole_dataset == 'USGS':
        sinks_dir = './karst_depression_polys_conus/'
        sinks_file = 'karst_depression_polys_conus.shp'
        polytag = 'karst_depression_polys_conus'
    elif sinkhole_dataset == 'Mihevc':
        sinks_dir = ''
        sinks_file = ''
        polytag = ''
    else:
        print('Invalid sinkhole_dataset parameter value of:', sinkhole_dataset)
        raise ValueError
    
    sinks = clip_shp_to_geometry(clipname='HUC-' + huc10_str + '-sinks-',
                                 shpdir=sinks_dir,
                                 shpfile = sinks_file,
                                 geom_df=this_hu10,
                                 outcrs=imgsrc_elev.crs)
    huc_sinks = gpd.read_file('./HUC-' + huc10_str + '-sinks-'+ polytag + '.shp')
    huc_sinks['ID'] = huc_sinks.index.values
    sinks_list = huc_sinks[['geometry','ID']].values.tolist()
    out_shape = imgsrc_elev.shape
    out_trans = imgsrc_elev.transform
    sinks_array = rasterio.features.rasterize(sinks_list,
                    fill=0, out_shape= out_shape,
                    transform = out_trans)
    profile = imgsrc_elev.profile
    sinks_raster = 'HUC-' + huc10_str + '-sinks-SinkholePolys.tif'
    with rasterio.open(sinks_raster, 'w', **profile) as dest:
        dest.write(sinks_array.astype(rasterio.int32), 1)
    
    
    wat_elev = calc_karst_fraction(datadir='./',
                                   demfile= os.path.join(rasterdir, rasterfile),
                                   sinksfile=sinks_raster,
                                   mean_filter=False)




