# sinkhole_analysis

*Notes on processing:*

To process bounding boxes (default filename bounding_boxes.xlsx), first run:

`python process-bouning-boxes.py -n NCPUS -s (USGS,Mihvec,or Combined)`

To overwrite results with exciting bbox csv files, use `--overwrite` flag.

To create QGIS project, run `create-QGIS-project.py (USGS,Mihevc, or Combined)`.

Then, for sharing run QGIS from conda env in `qgis` subdir on project file. Then activate QConsolidate plugin and export without zip. Zip the consolidated project for sharing.
