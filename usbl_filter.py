"""Filters USBL messages logged to a file for data of interest.

Writes all messages received to seperate file targets.

Example: python usbl_filter.py -t ./data/raw_usbl.txt -f ./ -n dive613
Reads in all USBL messages logged to ./data/raw_usbl.txt and writes
filtered status messages to ./dive613_usbl_{sentry, ship, jason, ctd}.txt.

Authors: Genevieve Flaspohler and Victoria Preston
Update: August 2023
Contact: {geflaspo, vpreston}@mit.edu
"""
import os
import yaml
import argparse
from filter_utils import parse_usbl_payload

# Get the USBL string IDs for each of the targets
with open("port_config.yaml") as f:
    globes = yaml.safe_load(f)
TARGET_IDS = globes["target_ids"]
TARGET_NAMES = globes["target_names"]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--target", action="store", type=str,
                        help="Where to look for raw data.",
                        default="./raw_usbl.txt")
    parser.add_argument("-f", "--filepath", action="store", type=str,
                        help="Write data at this filepath.",
                        default="./")
    parser.add_argument("-n", "--name", action="store", type=str,
                        help="Write data to a file with this name.",
                        default="")
    # Create commandline parser
    parse = parser.parse_args()

    # Parse commandline input
    filepath = parse.filepath
    name = parse.name
    raw_file = parse.target
    queue_files = [os.path.join(filepath, f"{name}_{q}.txt")
                   for q in TARGET_NAMES]

    # Now parse the file target by polling and parsing any new lines
    last_line = 0
    while(1):
        # Idle if no file
        if not os.path.isfile(raw_file):
            continue

        # Convert raw file to various processed files
        f = open(raw_file, "r").read()
        lines = f.split("\n")
        if last_line == len(lines)-1:  # get latest lines
            continue
        parse_lines = lines[last_line:]
        last_line = len(lines)-1

        # Populate data
        for line in parse_lines:
            # print(line)
            if len(line) == 0:
                continue
            parse_usbl_payload(line,
                               queue_files,
                               TARGET_IDS)
