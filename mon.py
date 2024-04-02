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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import datetime
import logging
import time
import random
import os
import sys

import meshtastic
import meshtastic.tcp_interface
from meshtastic.__init__ import LOCAL_ADDR

from pubsub import pub

import plugin.prometheus
import plugin.mqtt
import plugin.message_logger
import plugin.aprs

logging.basicConfig(format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

from plugin import call_plugin_function, register_plugin

MESHTASTIC_HOST=os.environ.get("MESHTASTIC_HOST", 'localhost')

register_plugin('prometheus.Prometheus_Plugin')
register_plugin('message_logger.MessageLogger_Plugin')
register_plugin('aprs.APRS_Plugin')
register_plugin('mqtt.MQTT_Plugin')
register_plugin('gpsd.GPSd_Plugin')

def OnMeshDisconnect(interface):
    sys.exit("Connection Lost to Meshtastic Node")

def OnMeshConnection(interface, topic=pub.AUTO_TOPIC):
    nodeInfo = interface.getMyNodeInfo()
    logger.info(f"Connected to node: userId={nodeInfo['user']['id']} hwModel={nodeInfo['user']['hwModel']}")
    #logger.info(nodeInfo)
    #interface.showInfo()
    x = interface.getNode(LOCAL_ADDR, requestChannels=True)
    #for c in x.channels:
    #    logger.info(c)

def OnMeshReceive(packet, interface):
    sender = packet.get('fromId', packet.get('from'))
    to = packet.get('toId')
    ch = packet.get('channel', None)
    dch = "Default" if ch is None else ch

    decoded = packet.get('decoded')
    port = decoded.get('portnum')

    if port == 'SIMULATOR_APP':
        ins = decoded.get('simulator',{}).get('portnum')
        logger.info(f"SIM {dch}/{ins} <<< {sender} >>> {to}")
        call_plugin_function('count_packets', interface, 'SIM', sender, ins)

    else:
        frm = "(No Details)"
        if sender in interface.nodes:
            frm = f"({interface.nodes[sender]['user']['shortName']} {interface.nodes[sender]['user']['longName']})"


        logger.info(f"LCL {dch}/{port} <<< {sender} {frm} >>> {to}")
        logger.debug(f"LCL {packet}")

        call_plugin_function(f'handle_{port}', interface, sender, packet)
        call_plugin_function('count_packets', interface, 'LOCAL', sender, port)

def connect_mesh():
    logger.info(f"Conneting to {MESHTASTIC_HOST}")
    try:
        interface = meshtastic.tcp_interface.TCPInterface(hostname=MESHTASTIC_HOST)
    except:
        sys.exit(f'Unable to connect to Meshtastic Node {MESHTASTIC_HOST}')
    return interface


if __name__ == '__main__':

    pub.subscribe(OnMeshReceive, "meshtastic.receive")
    pub.subscribe(OnMeshConnection, "meshtastic.connection.established")
    pub.subscribe(OnMeshDisconnect, "meshtastic.meshtastic.connection.lost")

    interface=connect_mesh()
    call_plugin_function('start', interface)

    while True:
        time.sleep(1)
        call_plugin_function('loop', interface)

