"""Filters SENTRY messages logged to a file for data of interest.

Writes all messages received from seperate queues to seperate file targets.

Example: python sentry_filter.py -t ./data/raw_dive617.txt -f ./ -n dive617
File reads in raw data stored in ./data/raw_dive617.txt and writes filtered
science, status, or instrument data
to ./dive617_sentry_{status, science, instrument}.

Authors: Genevieve Flaspohler and Victoria Preston
Update: August 2022
Contact: {geflaspo, vpreston}@mit.edu
"""
import os
import argparse
from filter_utils import filter_sentry_science_message, \
    filter_sentry_status_message, filter_experimental_message, parse_sentry_payload

# Globals which may need to change
STATUS_QUEUE = 0
SCIENCE_QUEUE = 34

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--target", action="store", type=str,
                        help="Where to look for raw data.",
                        default="./raw_dive_default.txt")
    parser.add_argument("-f", "--filepath", action="store", type=str,
                        help="Write data at this filepath.",
                        default="./")
    parser.add_argument("-n", "--name", action="store", type=str,
                        help="Write data to a file with this name.",
                        default="proc")
    # Create commandline parser
    parse = parser.parse_args()

    # Parse commandline input
    name = parse.name
    filepath = parse.filepath
    raw_file = parse.target
    queue_names = ["status", "science", "experimental"]
    queue_filters = [filter_sentry_status_message,
                     filter_sentry_science_message,
                     filter_experimental_message]
    queue_files = [os.path.join(
        filepath, f"{name}_sentry_{q}.txt") for q in queue_names]

    # Now parse the file target by polling and parsing any new lines
    last_line = 0
    while(1):
        # Idle if no file with raw data
        if not os.path.isfile(raw_file):
            continue

        # Convert raw file to various processed files
        f = open(raw_file, "r").read()
        lines = f.split("\n")
        if last_line == len(lines)-1:  # grab latest lines
            continue
        parse_lines = lines[last_line:]
        last_line = len(lines)-1

        # Populate data
        for i, line in enumerate(parse_lines):
            if len(line) == 0:
                continue

            msg_type, payload, timestamp = parse_sentry_payload(line, STATUS_QUEUE, SCIENCE_QUEUE)

            if msg_type is None:  # only care about certain queues
                continue

            # Get the matching queue index for message type
            qidx = queue_names.index(msg_type)

            # Filter the data
            data = queue_filters[qidx](payload)
            if data is None:
                continue

            # Log the filtered data
            if os.path.isfile(queue_files[qidx]):
                mode = "a"
            else:
                mode = "w+"
            print(timestamp)
            print(data)
            with open(queue_files[qidx], mode) as rf:
                rf.write(f"{timestamp+','+data}\n")
                rf.flush()
