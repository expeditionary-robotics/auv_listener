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
                        default="_usbl_sentry.txt")
    parser.add_argument("-b", "--bathy", action="store", type=str,
                        help="Read data for map underlay in this file.",
                        default="")
    parser.add_argument("-c", "--current", action="store", type=str,
                        help="Read data for current vectors.",
                        default="None")
    parser.add_argument("-m", "--mets", action="store", type=str,
                        help="Read methane data from mets file.",
                        default="None")
    parser.add_argument("-o", "--backscatter", action="store", type=str,
                        help="Read obs data from backscatter sensor.",
                        default="None")
    parser.add_argument("-k", "--keys", action="store", type=str,
                        help="Keys for plots and analysis",
                        default="Turbidity,ORP,Depth,Temperature,Salinity,Oxygen,dORPdt_log")
    parser.add_argument("-n", "--numkey", action="store", type=int,
                        help="Number of keys to display on quickview as default.",
                        default=6)
    # Create commandline parser
    parse = parser.parse_args()

    # Parse commandline input
    sentryname = parse.target
    sensorname = parse.experimental
    metsname = parse.mets
    usblname = parse.usbl
    backscattername = parse.backscatter
    bathyname = parse.bathy
    currentname = parse.current
    keys = str(parse.keys)
    numkeys = int(parse.numkey)

    # Create the dashboard
    tp = SentryDashboard(sentryname, sensorname, metsname, backscattername, usblname, bathyname, currentname, keys, numkeys)
