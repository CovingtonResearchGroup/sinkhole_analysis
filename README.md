# sinkhole_analysis

### Analysis of percent karst drainage

`p_karst_comparison.ipynb` - This notebook contains functions for comparing karst percentage to potential controls. The example here uses Chelsa Climate layers (which are not in the repo).

### Initial data download and processing for karst percentage calculations

Many of these scripts are designed to be run from the command line and have command-line options. 

`retrieve-dems-for-hucs-on-carbs.py` - Script to download all hucs containing carbonates and sinks. Relies on a shapefile that is not in the repo. Downloads all DEMs into a single subdirectory.

`process-dem-folder.py` - Script to conduct flow routing into sinks on all DEMs in a folder and calculate karst percentage.

`gis_functions.py`, `karstification.py`, and `sinkhole_functions.py` all contain functions for use in processing DEMs.

`polygonize_catchments.py` contains code to convert sinkhole catchment rasters into shapefiles and merge them into a single gdb file.

### Contents of subdirectories

`bbox_scripts/` contains original scripts used with bounding boxes. They likely won't run correctly without bringing them back up to the top level directory.

`scratch/` contains notebooks used during development of various scripts.

`old/` Old development code or scripts no longer used.

`USGS-Karst-Map/` contains the USGS Karst map layers, including some merged layers used in identifying HUCs that intersect carbonates.

`combined-sinkholes/` contains the combined sinkhole dataset used in flow routing.

`karst_depression_poly_conus/` contains the USGS sinkhole dataset.

`us-dolines-mihevc/` contains the sinkhole dataset generating by Mihevc and Mihevc using deep learning.











--------------------------
### Using bounding box scripts (old)

*Notes on processing:*

To process bounding boxes (default filename bounding_boxes.xlsx), first run:

`python process-bouning-boxes.py -n NCPUS -s (USGS,Mihvec,or Combined)`

To overwrite results with exciting bbox csv files, use `--overwrite` flag.

To create QGIS project, run `create-QGIS-project.py (USGS,Mihevc, or Combined)`.

Then, for sharing run QGIS from conda env in `qgis` subdir on project file. Then activate QConsolidate plugin and export without zip. Zip the consolidated project for sharing.

Finally, you can create collated csv file with HUC info and karst percentages by running `python collate-outputs.py (USGS,Mihevc,Combined)`.