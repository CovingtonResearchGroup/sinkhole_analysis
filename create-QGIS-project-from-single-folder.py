from qgis.core import (
    QgsProject,
    QgsApplication,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsLayerTreeGroup,
    QgsPalettedRasterRenderer,
    QgsRandomColorRamp,
    QgsCoordinateReferenceSystem,
    QgsSymbol,
    QgsRendererCategory,
    QgsStyle,
    QgsCategorizedSymbolRenderer,
    QgsFillSymbol,
    QgsSingleSymbolRenderer,
)
import glob
import os
import sys
import argparse
import shutil
import click


def create_project(sinks_tag="Combined", out_dir=None, dem_dir=None, overwrite=False):
    full_path = os.path.abspath(out_dir)
    if os.path.isdir(out_dir):
        if overwrite:
            if click.confirm(
                "Do you really want to delete: " + full_path, default=False
            ):
                shutil.rmtree(full_path)
            else:
                print("Exiting from program because output directory contains files.")
        else:
            print(
                "Exiting from program because output directory exists and overwrite flag was not set. "
                + full_path
            )

    os.makedirs(out_dir, exist_ok=True)
    # Create subfolders for layers
    karst_dir = os.path.join(out_dir, "karst-map/")
    os.makedirs(karst_dir)
    misc_dir = os.path.join(out_dir, "misc/")
    os.makedirs(misc_dir)
    sinks_dir = os.path.join(out_dir, "sinks/")
    os.makedirs(sinks_dir)
    analysis_dir = os.path.join(out_dir, "analysis-layers/")
    os.makedirs(analysis_dir)

    # Copy GIS layer files into their folders
    for file in glob.glob(r"./combined-sinkholes/combined-sinkholes-dissolved-5070.*"):
        shutil.copy(file, sinks_dir)
    for file in glob.glob(r"./USGS-Karst-Map/Carbonates48.*"):
        shutil.copy(file, karst_dir)
    for file in glob.glob(r"./misc/*"):
        shutil.copy(file, misc_dir)
    shutil.copy("./carb_huc_dems/merged_catchments.gpkg", analysis_dir)
    for file in glob.glob(r"./carb_huc_dems/processed_hucs.*"):
        shutil.copy(file, analysis_dir)

    QgsApplication.setPrefixPath("/home/mcoving/mambaforge/envs/geo/bin/qgis", True)

    qgs = QgsApplication([], False)
    qgs.initQgis()

    # Create a project instance
    project = QgsProject.instance()
    crs = QgsCoordinateReferenceSystem("EPSG:5070")
    project.setCrs(crs)

    root = project.layerTreeRoot()

    sinks_group = root.addGroup("Sinks")
    sinks_layer = QgsVectorLayer(
        os.path.join(sinks_dir, "combined-sinkholes-dissolved-5070.shp"), "Sinks", "ogr"
    )
    project.addMapLayer(sinks_layer, False)
    symbol = QgsFillSymbol.createSimple({"color": "#FFFFFF"})
    renderer = QgsSingleSymbolRenderer(symbol)

    sinks_layer.setRenderer(renderer)

    sinks_layer.setOpacity(0.5)

    sinks_layer.triggerRepaint()
    sinks_group.addLayer(sinks_layer)
    sinks_group.setExpanded(False)

    # root.insertLayer(2, WMSLayer)
    catchment_group = root.addGroup("Catchments")
    catchment_layer = QgsVectorLayer(
        os.path.join(analysis_dir, "merged_catchments.gpkg"), "Catchments", "ogr"
    )
    project.addMapLayer(catchment_layer, False)
    raster_val = catchment_layer.fields().lookupField("raster_val")
    unique_values = catchment_layer.uniqueValues(raster_val)

    categories = []
    for value in unique_values:
        symbol = QgsSymbol.defaultSymbol(catchment_layer.geometryType())
        category = QgsRendererCategory(value, symbol, str(value))
        categories.append(category)

    renderer = QgsCategorizedSymbolRenderer("raster_val", categories)
    renderer.updateColorRamp(QgsRandomColorRamp())
    catchment_layer.setRenderer(renderer)
    catchment_layer.triggerRepaint()

    catchment_layer.setOpacity(0.3)

    catchment_group.addLayer(catchment_layer)
    catchment_group.setExpanded(False)

    p_karst_layer = QgsVectorLayer(
        os.path.join(analysis_dir, "processed_hucs.shp"),
        "Carbonate HUCs",
        "ogr",
    )
    p_karst_layer.setOpacity(0.5)
    # project.addMapLayer(p_karst_layer, False)
    # root.addLayer(p_karst_layer)
    root.addMapLayer(p_karst_layer, False)

    karst_group = root.addGroup("USGS Karst Map")
    karst_layer = QgsVectorLayer(
        os.path.join(karst_dir, "Carbonates48.shp"), "Carbonates 48", "ogr"
    )
    project.addMapLayer(karst_layer, False)
    rock_type = karst_layer.fields().lookupField("ROCKTYPE1")
    unique_values = karst_layer.uniqueValues(rock_type)

    categories = []
    for value in unique_values:
        symbol = QgsSymbol.defaultSymbol(karst_layer.geometryType())
        category = QgsRendererCategory(value, symbol, str(value))
        categories.append(category)

    renderer = QgsCategorizedSymbolRenderer("ROCKTYPE1", categories)
    renderer.updateColorRamp(QgsRandomColorRamp())
    karst_layer.setRenderer(renderer)
    karst_layer.triggerRepaint()

    karst_layer.setOpacity(0.3)

    karst_group.addLayer(karst_layer)
    karst_group.setExpanded(False)

    states_layer = QgsVectorLayer(
        os.path.join(misc_dir, "cb_2018_us_state_500k.shp"), "US States", "ogr"
    )
    states_layer.setOpacity(0.5)
    # project.addMapLayer(states_layer, False)
    # root.addLayer(states_layer)
    root.addMapLayer(states_layer, False)

    dem_group = root.addGroup("Hillshade")
    url_with_params = "contextualWMSLegend=0&crs=EPSG:4326&dpiMode=7&featureCount=10&format=image/tiff&layers=3DEPElevation:Hillshade%20Gray&styles&url=https://elevation.nationalmap.gov/arcgis/services/3DEPElevation/ImageServer/WMSServer"
    WMSLayer = QgsRasterLayer(url_with_params, "3DEP Hillshade", "wms")
    project.addMapLayer(WMSLayer, False)
    dem_group.addLayer(WMSLayer)
    dem_group.setExpanded(False)

    # Collapse whole tree
    nodes = root.children()
    for n in nodes:
        if isinstance(n, QgsLayerTreeGroup):
            if n.isExpanded() is True:
                n.setExpanded(False)
                print(f"Layer group '{n.name()}' now collapsed.")

    project.write(os.path.join(out_dir, "US-Karstification-" + sinks_tag + ".qgs"))

    qgs.exitQgis()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--sinks",
        help="Which sinks shapefile to use (default=Combined).",
        choices=["USGS", "Mihevc", "Combined"],
        default="Combined",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="If flag is set, then existing QGIS project files will be overwritten.",
    )

    parser.add_argument(
        "-d",
        "--dir",
        help="Name of directory containing dems.",
        default="./carb_huc_dems",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        help="Name of directory to create QGIS project.",
        default="./share",
    )
    args = parser.parse_args()
    sinks = args.sinks
    overwrite = args.overwrite
    dem_dir = args.dir
    out_dir = args.outdir

    create_project(
        sinks_tag=sinks, overwrite=overwrite, dem_dir=dem_dir, out_dir=out_dir
    )
