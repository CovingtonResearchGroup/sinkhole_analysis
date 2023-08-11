from qgis.core import (
    QgsProject,
    QgsApplication,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsLayerTreeGroup,
    QgsPalettedRasterRenderer,
    QgsRandomColorRamp,
    QgsCoordinateReferenceSystem,
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

    for box in box_dirs:
        boxname = box.split("/")[-2]
        print("Boxname=", boxname)
        huc_dirs = glob.glob(box + "/*[0-9]/")
        box_group = root.addGroup(boxname)
        sinkhole_group = box_group.addGroup("Sinkholes")
        catchment_group = box_group.addGroup("Catchments")

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
                rasterLayer.setOpacity(0.5)

            # map_layers.append(rasterLayer)
            # catchment_group.insertLayer(0,rasterLayer)

            vector_path = os.path.join(huc, huc_num + "-" + sinks_tag + "-sinks.shp")
            if os.path.exists(vector_path):
                vectorLayer = QgsVectorLayer(
                    vector_path, "Sinkhole polygons " + huc_num, "ogr"
                )
                project.addMapLayer(vectorLayer, False)
                sinkhole_group.addLayer(vectorLayer)
                vectorLayer.setOpacity(0.5)
            # sinkhole_group.insertLayer(0, vectorLayer)
            # map_layers.append(vectorLayer)

        boxLayer = QgsVectorLayer(
            os.path.join(box, boxname + ".shp"), "Bounding box " + boxname, "ogr"
        )
        project.addMapLayer(boxLayer, False)
        box_group.addLayer(boxLayer)
        boxLayer.setOpacity(0.2)

        hucsLayer = QgsVectorLayer(
            os.path.join(box, "box_hucs.shp"), "HUCS for " + boxname, "ogr"
        )
        project.addMapLayer(hucsLayer, False)
        box_group.addLayer(hucsLayer)
        hucsLayer.setOpacity(0.3)

        sinkhole_group.setExpanded(False)
        catchment_group.setExpanded(False)
        box_group.setExpanded(False)
        # project.addMapLayers([rasterLayer, vectorLayer, WMSLayer])

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
            if n.isExpanded() == True:
                n.setExpanded(False)
                print(f"Layer group '{n.name()}' now collapsed.")

    project.write("./qgis/Sink-catchments" + sinks_tag + ".qgs")

    qgs.exitQgis()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sinks = sys.argv[1]
        create_project(sinks_tag=sinks)
    else:
        create_project()
