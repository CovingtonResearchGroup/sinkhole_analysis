import argparse
import glob
import os


def remove_files(regex):
    outs = glob.glob(regex, recursive=True)
    print(outs)
    confirm = input("Remove these files (y/n)? ")
    if confirm == "y":
        for f in outs:
            if os.path.isfile(f):
                os.remove(f)


def remove_whitebox_outputs():
    remove_files("./qgis/**/*pitfill.tif")
    remove_files("./qgis/**/*smoothed.tif")
    remove_files("./qgis/**/*d8.tif")


def remove_dems():
    remove_files("./qgis/**/*3DEP.tif")


def remove_box_dir_outputs(arg):
    if arg == "all":
        remove_files("./qgis/*/*")
    else:
        remove_files("./qgis/**/" + arg + "*.csv")


def remove_sink_files(arg):
    if arg == "all":
        remove_files("./qgis/**/*sinks.*")
    else:
        remove_files("./qgis/**/*" + arg + "-sinks.*")


def remove_catchment_files(arg):
    if arg == "all":
        remove_files("./qgis/**/*catchments.tif")
    else:
        remove_files("./qgis/**/*" + arg + "-catchments.tif")


def remove_all_but_dem():
    remove_whitebox_outputs()
    remove_box_dir_outputs("all")
    remove_sink_files("all")
    remove_catchment_files("all")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w",
        "--whitebox",
        help="Remove intermediate whitebox output files.",
        action="store_true",
    )
    parser.add_argument(
        "-d",
        "--dem",
        help="Remove HUC dem files.",
        action="store_true",
    )
    parser.add_argument(
        "-b",
        "--box",
        help="Remove box directory output files.",
        choices=["USGS", "Mihevc", "all"],
    )
    parser.add_argument(
        "-c",
        "--catchment",
        help="Remove sinkhole catchment files.",
        choices=["USGS", "Mihevc", "all"],
    )

    parser.add_argument(
        "-s",
        "--sinks",
        help="Remove HUC sink files.",
        choices=["USGS", "Mihevc", "all"],
    )
    parser.add_argument(
        "-a",
        "--all",
        help="Remove all output files but dem files.",
        action="store_true",
    )
    args = parser.parse_args()

    if args.all:
        remove_all_but_dem()
    else:
        if args.whitebox:
            remove_whitebox_outputs()
        if args.dem:
            remove_dems()
        if args.box:
            remove_box_dir_outputs()
        if args.sinks is not None:
            remove_sink_files(args.sinks)
        if args.catchment is not None:
            remove_catchment_files(args.catchment)
