import glob, os

demfiles = []

boxdirs = glob.glob("qgis/*")
for boxdir in boxdirs:
    huc_dirs = glob.glob(boxdir + "/*[0-9]/")
    for huc in huc_dirs:
        huc_num = huc.split("/")[-2]
        old_dem_path = os.path.join(huc, huc_num + "-USGS.tif")
        if os.path.isfile(old_dem_path):
            demfiles.append(old_dem_path)

newdemfiles = []
for demfile in demfiles:
    pathsplit = os.path.split(demfile)
    demdir = pathsplit[0]
    oldfile = pathsplit[1]
    newfile = oldfile[:-8] + "3DEP.tif"
    newdemfiles.append(newfile)
    newdempath = os.path.join(demdir, newfile)
    print("Renaming", oldfile)
    os.rename(demfile, newdempath)
