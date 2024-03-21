import datetime
import meshtastic
import meshtastic.tcp_interface
import json
import pprint
import logging
import time
import random

from prometheus_client import start_http_server, Summary, Counter, Gauge

from pubsub import pub

logging.basicConfig()

logger = logging.getLogger(name="meshtastic.stat")
logger.setLevel(logging.DEBUG)

interface = meshtastic.tcp_interface.TCPInterface(hostname="localhost")

RADIO_PACKETS_PORT = Counter('radio_packets_app', 'Radio Packets by App', ['portnum'])
RADIO_PACKETS_SENDER = Counter('radio_packets_sender', 'Radio Packets by Sender', ['sender'])

LOCAL_PACKETS_PORT = Counter('local_packets_app', 'Local Packets by App', ['portnum'])
LOCAL_PACKETS_SENDER = Counter('local_packets_sender', 'Local Packets by Sender', ['sender'])

NODE_CH_UTILISATION = Gauge('node_channel_util', 'Node Telemetry Channel Utilisation', ['sender'])
NODE_AIRTX_UTILISATION = Gauge('node_airtx_util', 'Node Telemetry Air TX Utilisation', ['sender'])

DATA = {}

def onConnection(interface, topic=pub.AUTO_TOPIC):
    nodeInfo = interface.getMyNodeInfo()
    logger.info(f"Connected to node: userId={nodeInfo['user']['id']} hwModel={nodeInfo['user']['hwModel']}")


def onReceive(packet, interface):
    sender = packet['fromId']
    to = packet.get('toId')
    decoded = packet.get('decoded')
    port = decoded.get('portnum')

    logger.info(f"\n\n====== {port} <<< {sender} >>> {to}")
    if port == 'SIMULATOR_APP':
        ins = decoded.get('simulator').get('portnum')
        logger.debug(f'Simulator Packet {ins}')
        pack = decoded.get('simulator')

        RADIO_PACKETS_PORT.labels(ins).inc()
        RADIO_PACKETS_SENDER.labels(sender).inc()

    else:
        pack = decoded

        if sender in interface.nodes:
            logger.debug(f"FROM: {interface.nodes[sender]['user']['shortName']} {interface.nodes[sender]['user']['longName']}")

        if '%s' % sender not in DATA:
            DATA['%s' % sender] = {}

        if port == 'POSITION_APP':
            logger.debug(f'Updated Position for {sender}')
            #DATA['%s' % sender]['position'] = pack.get('position')
            pprint.pprint(pack.get('position'))

        if port == 'TELEMETRY_APP':
            logger.debug('Updated Telemetry for %s' % sender)
            telem = pack.get('telemetry')
            pprint.pprint(telem)
            if 'deviceMetrics' in telem:
                NODE_CH_UTILISATION.labels(sender).set( telem['deviceMetrics'].get('channelUtilization') )
                NODE_AIRTX_UTILISATION.labels(sender).set( telem['deviceMetrics'].get('airUtilTx' ))

        if port == 'NODEINFO_APP':
            logger.debug('Updated Nodeinfo for %s' % sender)
            #DATA['%s' % sender]['user'] = pack.get('user')
            #pprint.pprint(pack.get('user'))

        if port == 'TEXTMESSAGE_APP':
            logger.debug('TEXT MESSAGE: %s' % pack)
            pprint.pprint(pack)

            #if '%s' % sender in DATA:
            #    #pprint.pprint(DATA['X%s' % sender])
            print('------')

        LOCAL_PACKETS_PORT.labels(port).inc()
        LOCAL_PACKETS_SENDER.labels(sender).inc()
        #pprint.pprint(pack)

def onLost(interface):
    logger.debug(f"Connecting to {interface.hostname} ...")
    devices[interface.device_name] = CustomTCPInterface(hostname=interface.hostname, device_name=interface.device_name)
    logger.debug(f"Connected to {interface.hostname}")


pub.subscribe(onReceive, "meshtastic.receive")
pub.subscribe(onConnection, "meshtastic.connection.established")
pub.subscribe(onLost, "meshtastic.connection.lost")


if __name__ == '__main__':
    start_http_server(8000)
    while True:
        time.sleep(1)


