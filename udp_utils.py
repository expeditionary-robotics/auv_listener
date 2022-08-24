"""Utilities file for UDP messages.

STAT_MESSAGE = b'>SMS:xxxx, var | -999.99 pos_ned goal_ned altitude heading hvel vvel batt_pct trackline abort_stat'
SCI_MESSAGE = b'>SMS:xxxx, var | fixed oxygen obs orp ctdtemp ctdsalt parodepth'
EXP_MESSAGE = b'>SMS:xxxx, var | laser_time,laser_temp,ringdown_ratio,fundamental_meth,aux_time,cell_temp,cell_press,house_temp,house_press,house_humid,states'

Authors: Genevieve Flaspohler and Victoria Preston
Update: August 2022
Contact: {geflaspo, vpreston}@mit.edu
"""


import numpy as np
import random
import datetime
import bagpy
import pandas as pd
import os


def process_acomms_bagfile(bagpointer):
    """Reads in a bagfile with UDP logs, for realistic data spoofing.

    Args:
        bagpointer (string): filepath to bagfile

    Returns:
        dataframe
    """
    bag = bagpy.bagreader(bagpointer)
    msg = bag.message_by_topic("/sentry/acomms/avtrak/modem/raw")
    df = pd.read_csv(msg)
    return df


def serve_acomms_msgs(df):
    """Serves a random acomms message"""
    byte_msgs = df['data']
    ascii_msgs = [m.split("b")[1].split("\\r")[0] for m in byte_msgs]
    ascii_msgs = [m for m in ascii_msgs if len(m) > 20 and "SMS" in m]
    return np.random.choice(ascii_msgs)


def usbl_message():
    """Creates spoofed usbl message.
    VFR 2019/09/24 13:27:58.033 2 0 SOLN_USBL -125.079565 44.489675 -597.900 0.000 10 0.00 0.00
    """
    front = np.random.choice(["VFR", "VPR"])
    measdate = datetime.datetime.now()
    vehicle_id = np.random.randint(0, 3)
    ship_id = np.random.randint(0, 3)
    solution = np.random.choice(["SOLN_USBL", "SOLN_SHIP", "SOLN"])
    lat = np.float32(np.random.rand(1)[0])
    long = np.float32(np.random.rand(1)[0])
    depth = np.float32(-1. * np.random.rand(1)[0])
    blah1 = 0.0
    blah2 = 10
    blah3 = 0.0
    blah4 = 0.0
    mess = str(front) + ' ' + str(measdate) + ' ' + str(vehicle_id) + ' ' + str(ship_id) + \
        ' ' + str(solution) + ' ' + str(lat) + ' ' + str(long) + ' ' + str(depth) + ' ' + \
        str(blah1) + ' ' + str(blah2) + ' ' + str(blah3) + ' ' + str(blah4)

    return mess


def sentry_status_message():
    """Creates spoofed sentry status message.
    SMS:5509,B1,R1,A0|SDQ 0:1294,3653,2514,64.6,352.0,1.00,-0.05,A0,0,31.5,1287,3688,2514,0,0,0,0,0,0,0,260
    """
    parts = ["SMS>blah|",  # front matter
             "SDQ 0:",  # queue_num
             str(round(random.random()*560))+",",  # pos_ned_x
             str(round(random.random()*230))+",",  # pos_ned_y
             str(round(random.random()*-134))+",",  # pos_ned_z
             str(round(random.random()*450, 1))+",",  # altitude
             str(round(random.random()*360, 1))+",",  # heading
             str(round(random.random()*5, 2))+",",  # hvel
             str(round(random.random()*5, 2))+",",  # vvel
             "A"+str(int(False))+",",  # abort
             str(0)+",",  # ins
             str(round(random.random(), 1)*100)+",",  # batt
             str(round(random.random())*560)+",",  # goal_ned_x
             str(round(random.random())*560)+",",  # goal_ned_y
             str(round(random.random())*-134)+",",  # goal_ned_z
             "0,0,0,0,0,0,0,",  # fill
             str(int(random.randint(0, 100)))]  # trackline
    mess = ""
    for m in parts:
        mess += m
    return mess


def sentry_science_message():
    """Creates spoofed sentry science message."""
    parts = ["SMS>blah|",  # front matter
             "SDQ 34:",  # queue_num
             str(round(random.random()*250, 2))+" ",  # o2
             str(round(random.random()*100, 2))+" ",  # obs
             str(round(random.random()*50, 2))+" ",  # orp
             str(round(random.random()*300, 2))+" ",  # temp
             str(round(random.random()*34, 2))+" ",  # salinity
             str(round(random.random()*2000, 2))]  # depth
    mess = ""
    for m in parts:
        mess += m
    return mess


def pythia_message():
    """Creates spoofed Pythia message, an experimental instrument."""
    lasertime = datetime.datetime.now()
    lasertemp = np.random.rand(1)[0]
    ringdown = np.random.rand(1)[0]
    methane = np.random.rand(1)[0]
    auxtime = np.random.rand(1)[0]
    celltemp = np.random.rand(1)[0]
    cellpres = np.random.rand(1)[0]
    housetemp = np.random.rand(1)[0]
    housepres = np.random.rand(1)[0]
    househum = np.random.rand(1)[0]
    states = [np.random.randint(0, 2) for m in range(6)]
    front = "SMS>blah|SDQ 101:"
    mess = front + str(lasertime) + ',' + str(lasertemp) + ',' + str(ringdown) + \
        ',' + str(methane) + ',' + str(auxtime) + ',' + str(celltemp) + ',' + str(cellpres) + \
        ',' + str(housetemp) + ',' + str(housepres) + \
        ',' + str(househum) + ',' + str(states)
    return mess


def sage_message():
    """Creates a spoofed SAGE message, an experimental instrument."""
    # 20210904T142137,5.9555,917,23.9,34
    front = "SMS>blah|SDQ 100:"
    ydt = "20210904T142137,"
    meas1 = str(np.round(np.random.rand(1)*10, 4)) + ","
    meas2 = str(np.random.randint(917, 1029)) + ","
    meas3 = str(np.round(np.random.rand(1)*24, 1)) + ","
    meas4 = str(np.random.randint(30, 40))
    mess = front + ydt + meas1 + meas2 + meas3 + meas4
    return mess
