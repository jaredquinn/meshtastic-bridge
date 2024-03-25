import datetime
import meshtastic
import meshtastic.tcp_interface
import logging
import time
import random

from pubsub import pub

logging.basicConfig()

logger = logging.getLogger(name="meshtastic.stat")
logger.setLevel(logging.DEBUG)

interface = meshtastic.tcp_interface.TCPInterface(hostname="localhost")

import plugin.prometheus
import plugin.mqtt
import plugin.message_logger

PLUGINS = {
  'prometheus': plugin.prometheus.Prometheus_Plugin(interface),
  'logger': plugin.message_logger.MessageLogger_Plugin(interface),
  'mqtt': plugin.mqtt.MQTT_Plugin(interface),
}


def OnMeshConnection(interface, topic=pub.AUTO_TOPIC):
    nodeInfo = interface.getMyNodeInfo()
    logger.info(f"Connected to node: userId={nodeInfo['user']['id']} hwModel={nodeInfo['user']['hwModel']}")

def OnMeshReceive(packet, interface):
    sender = packet['fromId']
    to = packet.get('toId')
    decoded = packet.get('decoded')
    port = decoded.get('portnum')

    if port == 'SIMULATOR_APP':
        ins = decoded.get('simulator',{}).get('portnum')
        logger.info(f"SIMPKT: {ins} <<< {sender} >>> {to}")
        call_plugin_function('count_packets', 'SIM', sender, ins)

    else:
        logger.info(f"LCLPKT: {port} <<< {sender} >>> {to}")
        pack = decoded
        if sender in interface.nodes:
            logger.debug(f"FROM: {interface.nodes[sender]['user']['shortName']} {interface.nodes[sender]['user']['longName']}")

        call_plugin_function(f'handle_{port}', sender, pack)
        call_plugin_function('count_packets', 'LOCAL', sender, port)


pub.subscribe(OnMeshReceive, "meshtastic.receive")
pub.subscribe(OnMeshConnection, "meshtastic.connection.established")

def call_plugin_function(fn, *args, **kwargs):
  for k, v in PLUGINS.items():
      fnc = getattr(v, fn, None)
      if callable(fnc):
          fnc(*args, **kwargs)

if __name__ == '__main__':
    call_plugin_function('start')
    while True:
        time.sleep(1)
        call_plugin_function('loop')

