# 
# This file is part of the meshtastic monitoring bridge distribution
# (https://github.com/jaredquinn/meshtastic-bridge).
# Copyright (c) 2024 Jared Quinn.
# 
# This program is free software: you can redistribute it and/or modify  
# it under the terms of the GNU General Public License as published by  
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License 

import logging
import json
import os
import gpsd

GPSD_HOST = os.environ.get('GPSD_HOST', None)
GPSD_PORT = os.environ.get('GPSD_PORT', 2947)

UPDATE_SECONDS = os.environ.get('MESH_LOCATION_UPDATE', 600)
LOCATION_SOURCE = os.environ.get('MESH_LOCATION_SOURCE', None)

__PLUGIN_NAME__ = 'gpsd'
logger = logging.getLogger(__name__)

class GPSd_Plugin:

    def __init__(self):
        self._count = 0
        if LOCATION_SOURCE != 'gpsd':
            logger.warning("Node Location is not aquired from GPSd; Plugin is inactive.")
            return

    def start(self, interface=None):
        if GPSD_HOST is not None:
            logger.info(f"Connecting to GPS Server {GPSD_HOST}:{GPSD_PORT}")
            gpsd.connect(host=GPSD_HOST, port=GPSD_PORT)
        else:
            logger.info(f"Connecting to Local GPS Server")
            gpsd.connect()


    def loop(self, interface=None):
        if LOCATION_SOURCE != 'gpsd':
            return

        if UPDATE_SECONDS != 0:
            self._count = self._count + 1
            if self._count >= int(UPDATE_SECONDS):
                packet = gpsd.get_current()
                logger.info(packet)
                logger.info(f'Updating Position with {packet.lat}, {packet.lon} at {packet.alt}m elevation')
                res = interface.sendPosition(
                   latitude=float(packet.lat),
                   longitude=float(packet.lon),
                   altitude=float(packet.alt)
                )
                self._count = 0

