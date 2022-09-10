"""Spoofs acoustic communications messages over UDP.

Example usage: 
python spoofer.py -i 127.0.0.1 -p 100 -f ./messages_to_spoof.txt -r 20
Reads a messages_to_spoof.txt file line by line and publishes
over the network 127.0.0.1 to port 100 every 20 seconds. 
If file is not provided random message formats are selected
and populated from a utils file.

Authors: Genevieve Flaspohler and Victoria Preston
Update: August 2022
Contact: {geflaspo, vpreston}@mit.edu
"""

import argparse
import socket
import time
import numpy as np
from udp_utils import sentry_science_message, sentry_status_message, pythia_message

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--ip", action="store",
                    type=str, help="IP address for spoofer.",
                    default="127.0.0.1")
parser.add_argument("-p", "--port", action="store", type=str,
                    help="Port for spoofer.",
                    default="52464")
parser.add_argument("-f", "--file", action="store", type=str,
                    help="If set, publish line by line from input file.",
                    default=None)
parser.add_argument("-r", "--rate", action="store", type=str,
                    help="Sets rate for publishing messages.", default="20")

# Create commandline parser
parse = parser.parse_args()

# Parse commandline input
ACOMMS_IP = parse.ip
ACOMMS_PORT = int(parse.port)
ACOMMS_PUB_RATE = float(parse.rate)
file = parse.file

sock = socket.socket(socket.AF_INET,
                     socket.SOCK_DGRAM)

if file is not None:
    data = open(file, 'r').read()
    lines = data.split('\n')
    num_lines = len(lines)
    while(1):
        realline = np.random.randint(0, num_lines)
        msg = np.random.choice([lines[realline], sentry_science_message()])
        if len(msg) > 1:
            print(msg)
            MESSAGE = bytes(msg, encoding="utf8")
            sock.sendto(MESSAGE, (ACOMMS_IP, ACOMMS_PORT))
            time.sleep(ACOMMS_PUB_RATE)
else:
    while(1):
        msg = np.random.choice(
            [sentry_status_message(), sentry_science_message(), pythia_message()])
        print(msg)
        sock.sendto(bytes(msg, encoding='utf8'), (ACOMMS_IP, ACOMMS_PORT))
        time.sleep(ACOMMS_PUB_RATE)
