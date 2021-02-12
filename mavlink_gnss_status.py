#!/usr/bin/env python3
"""
MyGalileoDrone - MAVLink GNSS Status Display

Display the GPS_STATUS messages of all connected systems in a nice way.

Author:    Jannik Beyerstedt <beyerstedt@consider-it.de>
Copyright: (c) consider it GmbH, 2021
"""

import argparse
import logging
import sys
import pymavlink.mavutil as mavutil

OWN_SYSID = 255
OWN_COMPID = 0
UDP_CONNECT_TIMEOUT = 10


if __name__ == "__main__":
    log_format = '%(asctime)s %(levelname)s:%(name)s: %(message)s'
    log_datefmt = '%Y-%m-%dT%H:%M:%S%z'
    logging.basicConfig(format=log_format, datefmt=log_datefmt, level=logging.INFO)
    logger = logging.getLogger()

    parser = argparse.ArgumentParser(description='MAVLink GNSS Status Display')
    parser.add_argument("-d", "--device", required=True,
                        help="connection address, e.g. tcp:$ip:$port, udpin:$ip:$port")
    parser.add_argument("-s", "--sysID", type=int,
                        help="just display data from the specified system ID")
    parser.add_argument("-v", "--verbosity", action="count",
                        help="increase output and logging verbosity")
    args = parser.parse_args()

    if args.verbosity == 2:
        logger.setLevel(logging.DEBUG)
    elif args.verbosity == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    # SETUP
    # open the connection
    try:
        mav = mavutil.mavlink_connection(
            args.device, source_system=OWN_SYSID, source_component=OWN_COMPID)
    except OSError:
        logger.error("MAVLink connection failed, exiting")
        sys.exit(-1)

    # when udpout, start with sending a heartbeat
    if args.device.startswith('udpout:'):
        i = 0
        logger.info("UDP out: sending heartbeat to initilize a connection")
        while True:
            mav.mav.heartbeat_send(OWN_SYSID, OWN_COMPID, base_mode=0,
                                   custom_mode=0, system_status=0)
            i += 1

            msg = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
            if msg is not None:
                break

            if i >= UDP_CONNECT_TIMEOUT:
                logger.error("UDP out: nothing received, terminating")
                sys.exit(-1)

            logger.debug("UDP out: retrying heartbeat")

    # RUN
    while True:
        msg = mav.recv_match(type='GPS_STATUS', blocking=True)
        logger.debug("Message from %d/%d: %s", msg.get_srcSystem(), msg.get_srcComponent(), msg)

        # just evaluate messages from specific system, if requested
        if args.sysID is not None and msg.get_srcSystem() != args.sysID:
            logger.debug("Ignore message from system %d", msg.get_srcSystem())
            continue

        # evaluate message
        satinfos = {"GPS": list(),
                    "SBAS": list(),
                    "Galileo": list(),
                    "BeiDou": list(),
                    "IMES": list(),
                    "QZSS": list(),
                    "GLONASS": list()
                    }

        for idx, _ in enumerate(msg.satellite_prn):
            sat_prn = msg.satellite_prn[idx]
            sat_snr = msg.satellite_snr[idx]
            sat_used = msg.satellite_used[idx]
            sat_azim = msg.satellite_azimuth[idx]
            sat_elev = msg.satellite_elevation[idx]

            # convert PRN to SV numbering
            sat_prn_str = ""
            satinfos_key = ""
            if 1 <= sat_prn <= 32:  # GPS 1-32 -> G1-G32
                sat_prn_str = "G" + str(sat_prn)
                satinfos_key = "GPS"
            elif 120 <= sat_prn <= 158:  # SBAS 120-158 -> S120-S158
                sat_prn_str = "S" + str(sat_prn)
                satinfos_key = "SBAS"
            elif 211 <= sat_prn <= 246:  # Galileo 211-24 -> E1-E36
                sat_prn_str = "E" + str(sat_prn - 210)
                satinfos_key = "Galileo"
            elif 159 <= sat_prn <= 163:  # BeiDou 159-163,33-64 -> B1-B37
                sat_prn_str = "B" + str(sat_prn - 158)
                satinfos_key = "BeiDou"
            elif 33 <= sat_prn <= 64:  # BeiDou 159-163,33-64 -> B1-B37
                sat_prn_str = "B" + str(sat_prn - 32)
                satinfos_key = "BeiDou"
            elif 173 <= sat_prn <= 182:  # IMES 173-182 -> I1-I10
                sat_prn_str = "I" + str(sat_prn - 172)
                satinfos_key = "IMES"
            elif 193 <= sat_prn <= 202:  # QZSS 193-202 -> Q1-A10
                sat_prn_str = "Q" + str(sat_prn - 192)
                satinfos_key = "QZSS"
            elif 65 <= sat_prn <= 96:  # GLONASS 65-96 -> R1-R32
                sat_prn_str = "R" + str(sat_prn - 64)
                satinfos_key = "GLONASS"
            else:
                break

            if satinfos_key:
                satinfos[satinfos_key].append((sat_prn_str, sat_snr, sat_used))
                logger.debug("Sat convert: %3d->%4s, SNR %2d, used %d, elev %3d, azim %3d",
                             sat_prn, sat_prn_str, sat_snr, sat_used, sat_elev, sat_azim)

        print("MAVLink sysid %d:" % (msg.get_srcSystem()))
        for gnss_system, satellites in satinfos.items():
            sat_list_str = "    " + gnss_system + ": "
            if satellites:
                for sat in satellites:
                    sat_list_str += sat[0] + ", "
                print(sat_list_str[:-2])
            # else:
            #     print(sat_list_str)
