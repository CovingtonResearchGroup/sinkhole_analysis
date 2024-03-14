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
)
import glob
import os
import sys


def create_project(sinks_tag="Combined"):
    QgsApplication.setPrefixPath("/home/mcoving/mambaforge/envs/geo/bin/qgis", True)

    qgs = QgsApplication([], False)
    qgs.initQgis()

    # Create a project instance
    project = QgsProject.instance()
    crs = QgsCoordinateReferenceSystem("EPSG:5070")
    project.setCrs(crs)

    root = project.layerTreeRoot()

    # root.insertLayer(2, WMSLayer)
    catchment_group = root.addGroup("Catchments")

    catchment_tifs = glob.glob("carb_huc_dems/catchments/*.tif/")
    print("catchment tifs =", catchment_tifs)
    for raster_path in catchment_tifs:
        huc_num = raster_path.split("/")[-1].split("-")[0]
        print("raster_path=", raster_path)
        if os.path.exists(raster_path):
            rasterLayer = QgsRasterLayer(
                raster_path, "Sinkhole basins " + huc_num, "gdal"
            )
            project.addMapLayer(rasterLayer, False)
            catchment_group.addLayer(rasterLayer)
            classes = QgsPalettedRasterRenderer.classDataFromRaster(
                rasterLayer.dataProvider(), 1, QgsRandomColorRamp()
            )
            paletted_renderer = QgsPalettedRasterRenderer(
                rasterLayer.dataProvider(), 1, classes
            )
            rasterLayer.setRenderer(paletted_renderer)
            rasterLayer.setOpacity(0.3)

    catchment_group.setExpanded(False)

    karst_group = root.addGroup("USGS Karst Map")
    karst_layer = QgsVectorLayer(
        "./USGS-Karst-Map/Carbonates48.shp", "Carbonates 48", "ogr"
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

    project.write("./carb_huc_dems/Sink-catchments-" + sinks_tag + ".qgs")

    qgs.exitQgis()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sinks = sys.argv[1]
        create_project(sinks_tag=sinks)
    else:
        create_project()
