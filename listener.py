"""UDP Listener for networked acoustic communications messages from AUV/USBL Systems.

Writes all messages received to a specified file target.

Example: python listener.py -i 127.0.0.1 -p 100 -f ./ -n dive614 -v
Listens to port 100 on 127.0.0.1 and writes all data heard there
to ./raw_dive614. All messages received are also printed verbosely
to terminal.

Authors: Genevieve Flaspohler and Victoria Preston
Update: August 2022
Contact: {geflaspo, vpreston}@mit.edu
"""
import os
import datetime
import argparse
import socket

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", action="store",
                        type=str, help="IP address of network.",
                        default="127.0.0.1")
    parser.add_argument("-p", "--port", action="store", type=str,
                        help="Port for listening.",
                        default="52464")
    parser.add_argument("-f", "--filepath", action="store", type=str,
                        help="Write data at this filepath.",
                        default="./")
    parser.add_argument("-n", "--name", action="store", type=str,
                        help="Write data to a file with this name.",
                        default="dive_default")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Whether to print data received to the terminal.",
                        default=False)

    # Create commandline parser
    parse = parser.parse_args()

    # Parse commandline input
    ACOMMS_IP = parse.ip
    ACOMMS_PORT = int(parse.port)
    filepath = parse.filepath
    name = parse.name
    verbose = parse.verbose

    raw_file = os.path.join(filepath, f"raw_{name}.txt")
    sock = socket.socket(socket.AF_INET,
                         socket.SOCK_DGRAM)

    sock.bind((ACOMMS_IP, ACOMMS_PORT))

    while True:
        data, addr = sock.recvfrom(2048)  # buffer size in bytes
        msgrecv = str(datetime.datetime.utcnow())

        if len(data) == 0:
            # check that message is populated
            continue

        data = str(data, encoding="utf8")
        if verbose is True:
            # print received message to terminal
            print(data)

        # Log the raw data
        if os.path.isfile(raw_file):
            mode = "a"
        else:
            mode = "w+"
        with open(raw_file, mode) as rf:
            rf.write(f"{msgrecv+'|'+data}\n")
            rf.flush()
