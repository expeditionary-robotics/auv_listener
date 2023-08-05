"""Plotly dashboard for live SENTRY data display and exploration.

Example: python sentry_dashboard.py -t ./test_sentry_science.txt -b ./bathy.txt -c 
Plots data from live-updating test_sentry_science.txt file using
the bathy.txt file as a map underlay.
Individual timeseries, and map will be made available.

Authors: Victoria Preston
Update: August 2023
Contact: vpreston@mit.edu
"""
import argparse
from plotter_utils import SentryDashboard


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--target", action="store", type=str,
                        help="Read sentry data from this file.",
                        default="proc_science.txt")
    parser.add_argument("-x", "--experimental", action="store", type=str,
                        help="Read methane data from this file.",
                        default="proc_experimental.txt")
    parser.add_argument("-u", "--usbl", action="store", type=str,
                        help="Read usbl data from this file.",
                        default="proc_usbl.txt")
    parser.add_argument("-c", "--continuous", action="store", type=bool,
                        help="Whether to read data continuously.",
                        default=False)
    parser.add_argument("-b", "--bathy", action="store", type=str,
                        help="Read data for map underlay in this file.",
                        default="")
    # Create commandline parser
    parse = parser.parse_args()

    # Parse commandline input
    sentryname = parse.target
    sensorname = parse.experimental
    usblname = parse.usbl
    bathyname = parse.bathy
    liveplot = parse.continuous

    # Create the dashboard
    tp = SentryDashboard(sentryname, sensorname, usblname, bathyname, liveplot)
