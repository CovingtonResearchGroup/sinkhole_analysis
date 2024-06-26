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


def create_project(sinks_tag="USGS"):
    QgsApplication.setPrefixPath("/home/mcoving/mambaforge/envs/geo/bin/qgis", True)

    qgs = QgsApplication([], False)
    qgs.initQgis()

    # Create a project instance
    project = QgsProject.instance()
    crs = QgsCoordinateReferenceSystem("EPSG:4326")
    project.setCrs(crs)

    root = project.layerTreeRoot()

    # root.insertLayer(2, WMSLayer)

    box_dirs = glob.glob("qgis/*/")
    box_dirs.sort()
    for box in box_dirs:
        boxname = box.split("/")[-2]
        print("Boxname=", boxname)
        huc_dirs = glob.glob(box + "/*[0-9]/")
        box_group = root.addGroup(boxname)
        sinkhole_group = box_group.addGroup("Sinkholes")
        catchment_group = box_group.addGroup("Catchments")
        carbs_hucs_group = box_group.addGroup("Carbonate only HUCS")

        for huc in huc_dirs:
            huc_num = huc.split("/")[-2]
            raster_path = os.path.join(
                huc, huc_num + "-" + sinks_tag + "-catchments.tif"
            )
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

            # map_layers.append(rasterLayer)
            # catchment_group.insertLayer(0,rasterLayer)

            vector_path = os.path.join(huc, huc_num + "-" + sinks_tag + "-sinks.shp")
            if os.path.exists(vector_path):
                vectorLayer = QgsVectorLayer(
                    vector_path, "Sinkhole polygons " + huc_num, "ogr"
                )
                project.addMapLayer(vectorLayer, False)
                sinkhole_group.addLayer(vectorLayer)
                vectorLayer.setOpacity(0.3)
            # sinkhole_group.insertLayer(0, vectorLayer)
            # map_layers.append(vectorLayer)

            carb_huc_path = os.path.join(huc, huc_num + '-carbs_only_huc.shp')
            if os.path.exists(carb_huc_path):
                carbHUCLayer = QgsVectorLayer(
                    carb_huc_path, "Carb HUC " + huc_num, "ogr"
                )
                project.addMapLayer(carbHUCLayer, False)
                carbs_hucs_group.addLayer(carbHUCLayer)
                carbHUCLayer.setOpacity(0.3)
                
        boxLayer = QgsVectorLayer(
            os.path.join(box, boxname + ".shp"), "Bounding box " + boxname, "ogr"
        )
        project.addMapLayer(boxLayer, False)
        box_group.addLayer(boxLayer)
        boxLayer.setOpacity(0.1)

        hucsLayer = QgsVectorLayer(
            os.path.join(box, "box_hucs.shp"), "HUCS for " + boxname, "ogr"
        )
        project.addMapLayer(hucsLayer, False)
        box_group.addLayer(hucsLayer)
        hucsLayer.setOpacity(0.2)

        sinkhole_group.setExpanded(False)
        catchment_group.setExpanded(False)
        box_group.setExpanded(False)
        carbs_hucs_group.setExpanded(False)
        # project.addMapLayers([rasterLayer, vectorLayer, WMSLayer])

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

    project.write("./qgis/Sink-catchments-" + sinks_tag + ".qgs")

    qgs.exitQgis()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sinks = sys.argv[1]
        create_project(sinks_tag=sinks)
    else:
        create_project()
