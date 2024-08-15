#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 14 12:05:55 2024

@author: charlesshobe
"""

def get_rock_types(huc, karst):
    huc_geom = huc.geometry
    huc_area = huc_geom.area
    huc12 = huc.huc12
    huc_rocks = karst[karst.intersects(huc_geom)]
    this_huc_rocks_list = []
    for j, rock in huc_rocks.iterrows():
        rock_poly = rock.geometry.intersection(huc_geom)
        percent_area = rock_poly.area / huc_area
        this_huc_rocks_list.append(
            {
                "huc12": huc12,
                "rocktype1": rock.ROCKTYPE1,
                "rocktype2": rock.ROCKTYPE2,
                "percent_area": percent_area,
                "induration": rock.Induration,
                "exposure": rock.Exposure,
                "unit_name": rock.UNIT_NAME,
                "unit_age": rock.UNIT_AGE,
            }
        )
    return this_huc_rocks_list