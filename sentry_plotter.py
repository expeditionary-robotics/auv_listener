"""Live plotter for SENTRY science data time series.

Example: python sentry_plotter.py -t ./test_sentry_science.txt -x 0 -y 1,2 -n O2,OBS -s
Plots data from live-updating test_sentry_science.txt file, in which
column 0 is a timestamp, and columns 1 and 2 (O2 and OBS) are to be plotted
in subplots. Everything is plotted as a scatter plot.

Authors: Genevieve Flaspohler and Victoria Preston
Update: August 2022
Contact: {geflaspo, vpreston}@mit.edu
"""
import argparse
from plotter_utils import LiveTimePlot


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--target", action="store", type=str,
                        help="Read data continuously from this file.",
                        default="proc_sentry_science.txt")
    parser.add_argument("-x", "--ax_index", action="store", type=int,
                        help="This is the index of the time column.",
                        default=0)
    parser.add_argument("-y", "--plot_index", action="store", type=str,
                        help="Plot these columns.",
                        default="1,2,3,4,5,6")
    parser.add_argument("-n", "--plot_names", action="store", type=str,
                        help="Name these columns.",
                        default="O2,OBS,ORP,Temperature,Salinity,Depth")
    parser.add_argument("-s", "--scatter", action="store_true",
                        help="Whether to plot as a scatter plot.",
                        default=False)
    # Create commandline parser
    parse = parser.parse_args()

    # Parse commandline input
    filename = parse.target
    ax_index = parse.ax_index
    scatter = parse.scatter
    col_index = parse.plot_index.split(",")
    col_index = [int(x) for x in col_index]
    col_names = parse.plot_names.split(",")
    col_names = [str(x) for x in col_names]

    tp = LiveTimePlot(filename, ax_index, col_index, col_names, scatter)
