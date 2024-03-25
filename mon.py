import datetime
import meshtastic
import meshtastic.tcp_interface
import logging
import time
import random

from pubsub import pub

import plugin.prometheus
import plugin.mqtt
import plugin.message_logger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


PLUGINS = {
  'prometheus': plugin.prometheus.Prometheus_Plugin(),
  'logger': plugin.message_logger.MessageLogger_Plugin(),
  'mqtt': plugin.mqtt.MQTT_Plugin(),
}



def OnMeshConnection(interface, topic=pub.AUTO_TOPIC):
    nodeInfo = interface.getMyNodeInfo()
    logger.info(f"Connected to node: userId={nodeInfo['user']['id']} hwModel={nodeInfo['user']['hwModel']}")
    logger.debug(nodeInfo)

def OnMeshReceive(packet, interface):
    sender = packet['fromId']
    to = packet.get('toId')
    decoded = packet.get('decoded')
    port = decoded.get('portnum')
    ch = packet.get('channel', None)

    if port == 'SIMULATOR_APP':
        ins = decoded.get('simulator',{}).get('portnum')
        logger.info(f"SIMPKT: {ch}/{ins} <<< {sender} >>> {to}")
        call_plugin_function('count_packets', interface, 'SIM', sender, ins)

    else:
        logger.info(f"LCLPKT: {ch}/{port} <<< {sender} >>> {to}")
        pack = decoded
        pack['_channel'] = ch

        if sender in interface.nodes:
            logger.debug(f"FROM: {interface.nodes[sender]['user']['shortName']} {interface.nodes[sender]['user']['longName']}")

        call_plugin_function(f'handle_{port}', interface, sender, pack)
        call_plugin_function('count_packets', interface, 'LOCAL', sender, port)


def call_plugin_function(fn, interface, *args, **kwargs):
  for k, v in PLUGINS.items():
      fnc = getattr(v, fn, None)
      if callable(fnc):
          fnc(*args, **kwargs, interface=interface)



if __name__ == '__main__':
    pub.subscribe(OnMeshReceive, "meshtastic.receive")
    pub.subscribe(OnMeshConnection, "meshtastic.connection.established")
    interface = meshtastic.tcp_interface.TCPInterface(hostname="localhost")
    call_plugin_function('start', interface)
    while True:
        time.sleep(1)
        call_plugin_function('loop', interface)


