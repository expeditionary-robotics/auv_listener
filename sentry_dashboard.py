"""Plotly dashboard for live SENTRY data display and exploration.

Example: python sentry_dashboard.py -t ./test_sentry_science.txt -b ./bathy.txt 
Plots data from live-updating test_sentry_science.txt file using
the bathy.txt file as a map underlay.
Individual timeseries, and map will be made available.

Authors: Victoria Preston
Update: August 2026
Contact: vpreston@olin.edu
"""
import argparse
import pandas as pd
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
    parser.add_argument("-v", "--vents", action="store", type=str,
                        help="Reads vent coordinates lat,lon from file.",
                        default="None")
    parser.add_argument("-e", "--equipment", action="store", type=str,
                        help="Reads mooring or equipment coordinates lat,lon from file.",
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
    ventsname = parse.vents
    equipmentname = parse.equipment
    keys = str(parse.keys)
    numkeys = int(parse.numkey)

    # Create persistent variables for passing through
    bathydata = pd.read_table(bathyname, names=["lon", "lat", "depth"], delim_whitespace=True).dropna()
    # Reduce bathy tile size for plotting purposes; otherwise rendering will take too long
    bathy_len = 1e10
    while bathy_len > 50000:
        bathydata = bathydata[::2]
        bathy_len = len(bathydata.lat)
    
    if ventsname != "None":
        ventdata = pd.read_csv(ventsname, names=["lat", "lon"]).dropna()
    else:
        ventdata = None

    if equipmentname != "None":
        equipmentdata = pd.read_csv(equipmentname, names=["lat", "lon"]).dropna()
    else:
        equipmentdata = None

    # Create the dashboard
    print("Creating dashboard...")
    tp = SentryDashboard(sentryfile=sentryname,
                         sensorfile=sensorname,
                         metsfile=metsname,
                         backscatterfile=backscattername,
                         usblfile=usblname,
                         bathydata=bathydata,
                         currentfile=currentname,
                         ventdata=ventdata,
                         equipmentdata=equipmentdata,
                         keys=keys,
                         numkeys=numkeys)
