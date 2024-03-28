import datetime
import logging
import time
import random
import os

import meshtastic
import meshtastic.tcp_interface
from meshtastic.__init__ import LOCAL_ADDR

from pubsub import pub

import plugin.prometheus
import plugin.mqtt
import plugin.message_logger
import plugin.aprs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from plugin import call_plugin_function, register_plugin

register_plugin('prometheus.Prometheus_Plugin')
register_plugin('message_logger.MessageLogger_Plugin')
register_plugin('aprs.APRS_Plugin')
register_plugin('mqtt.MQTT_Plugin')


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

    decoded = packet.get('decoded')
    port = decoded.get('portnum')

    if port == 'SIMULATOR_APP':
        ins = decoded.get('simulator',{}).get('portnum')
        logger.info(f"SIMPKT: {ch}/{ins} <<< {sender} >>> {to}")
        call_plugin_function('count_packets', interface, 'SIM', sender, ins)

    else:
        frm = "(No Details)"
        if sender in interface.nodes:
            frm = f"({interface.nodes[sender]['user']['shortName']} {interface.nodes[sender]['user']['longName']})"
        logger.info(f"LCLPKT: {ch}/{port} <<< {sender} {frm} >>> {to}")
        logger.debug(f"LCLPKT: {packet}")

        call_plugin_function(f'handle_{port}', interface, sender, packet)
        call_plugin_function('count_packets', interface, 'LOCAL', sender, port)


if __name__ == '__main__':
    MESHTASTIC_HOST=os.environ.get("MESHTASTIC_HOST", 'localhost')

    pub.subscribe(OnMeshReceive, "meshtastic.receive")
    pub.subscribe(OnMeshConnection, "meshtastic.connection.established")
    logger.info(f"Conneting to {MESHTASTIC_HOST}")

    interface = meshtastic.tcp_interface.TCPInterface(hostname=MESHTASTIC_HOST)
    call_plugin_function('start', interface)

    while True:
        time.sleep(1)
        call_plugin_function('loop', interface)


