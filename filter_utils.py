"""Utilities for building a filter file.

Authors: Genevieve Flaspohler and Victoria Preston
Update: August 2022
Contact: {geflaspo, vpreston}@mit.edu
"""

import os

def filter_sentry_status_message(message):
    """Strips the vehicle status message.
        vehicle_status_queue (SDQ 0)
        SentryVehicleState.msg
        float32 INVALID = -999.99 
        ds_acomms_msgs/Vector3_F32 pos_ned
        ds_acomms_msgs/Vector3_F32 goal_ned
        float32 altitude
        float32 heading
        float32 horz_velocity
        float32 vert_velocity
        float32 battery_pct
        uint16 trackline
        bool abort_status
    """
    try:
        return message
    except:
        return None


def filter_sentry_science_message(message):
    """Strips the vehicle science message.
        vehicle_scalar_science_queue (SDQ 4)
        SentryScalarScience.msg
        float32 oxygen_concentration
        float32 obs_raw
        float32 orp_raw
        float32 ctd_temperature
        float32 ctd_salinity
        float32 paro_depth
    """
    try:
        packet = str(message).split(" ")
        o2 = packet[0]
        obs = packet[1]
        orp = packet[2]
        temp = packet[3]
        salt = packet[4]
        depth = packet[5]
        return f"{o2},{obs},{orp},{temp},{salt},{depth}"
    except:
        return None


def filter_experimental_message(message):
    """Stand-in function for experimental sensors parsed in queue."""
    return str(message)


def parse_sentry_payload(message, status_queue, science_queue, experimental_queue):
    """Inspects the message and returns the message type.
    One of "status", "science", "experimental", or None
    Provide the message and queue targets for status, science, and experimental.
    Returns message type, message payload, and cleaned timestamp.
    """
    if not "SDQ" in message:
        return None, message, None

    payload = message[message.index("SDQ"):]
    timestamp = message.split("|")[0]

    # Starting from index 4 to remove leading "SDQ "
    try:
        queue = int(payload[4:payload.index(":")])
        payload = payload[payload.index(":")+1:]
        if queue == status_queue:
            return "status", payload, timestamp
        elif queue == science_queue:
            return "science", payload, timestamp
        elif queue == experimental_queue:
            return "experimental", payload, timestamp
        else:
            return None, message, timestamp
    except:
        return None, message, timestamp


def parse_usbl_payload(message, sentry_file_target, jason_file_target, ship_file_target, ctd_file_target, sentry_id, jason_id, ship_id, ctd_id):
    """Filters message of format:
    VFR 2019/09/24 13:27:58.033 2 0 SOLN_USBL -125.079565 44.489675 -597.900 0.000 10 0.00 0.00
    """
    mess = str(message)
    packets = mess.split(" ")
    new_stamp = packets[1].replace("/", "-")  # standadize timestamp
    # extract relevant info
    info = f"{new_stamp} {packets[2]},{packets[6]},{packets[7]},{packets[8]}"

    if "VFR" in packets[0]:
        if packets[4] == sentry_id and "USBL" in packets[5]:
            if os.path.isfile(sentry_file_target):
                mode = "a"
            else:
                mode = "w+"
            with open(sentry_file_target, mode) as rf:
                rf.write(f"{info}\n")
                rf.flush()
        elif packets[4] == jason_id and "USBL" in packets[5]:
            if os.path.isfile(jason_file_target):
                mode = "a"
            else:
                mode = "w+"
            with open(jason_file_target, mode) as rf:
                rf.write(f"{info}\n")
                rf.flush()
        elif packets[4] == ship_id and "SOLN_GPS0" in packets[5]:
            if os.path.isfile(ship_file_target):
                mode = "a"
            else:
                mode = "w+"
            with open(ship_file_target, mode) as rf:
                rf.write(f"{info}\n")
                rf.flush()
        elif packets[4] == ctd_id and "USBL" in packets[5]:
            if os.path.isfile(ctd_file_target):
                mode = "a"
            else:
                mode = "w+"
            with open(ctd_file_target, mode) as rf:
                rf.write(f"{info}\n")
                rf.flush()
        else:
            pass
    else:
        pass

    return