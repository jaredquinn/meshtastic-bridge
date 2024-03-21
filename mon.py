import datetime
import meshtastic
import meshtastic.tcp_interface
import json
import pprint
import logging
import time
import random

from prometheus_client import start_http_server, Summary, Counter

from pubsub import pub

logging.basicConfig()

logger = logging.getLogger(name="meshtastic.stat")
logger.setLevel(logging.DEBUG)

interface = meshtastic.tcp_interface.TCPInterface(hostname="localhost")

RADIO_PACKETS_PORT = Counter('radio_packets_app', 'Radio Packets by App', ['portnum'])
RADIO_PACKETS_SENDER = Counter('radio_packets_sender', 'Radio Packets by Sender', ['sender'])
LOCAL_PACKETS_PORT = Counter('local_packets_app', 'Local Packets by App', ['portnum'])
LOCAL_PACKETS_SENDER = Counter('local_packets_sender', 'Local Packets by Sender', ['sender'])

DATA = {}

def onConnection(interface, topic=pub.AUTO_TOPIC):
    nodeInfo = interface.getMyNodeInfo()
    logger.info(f"Connected to node: userId={nodeInfo['user']['id']} hwModel={nodeInfo['user']['hwModel']}")


def onReceive(packet, interface): # called when a packet arrives
    sender = packet['fromId']
    to = packet.get('toId')
    decoded = packet.get('decoded')
    port = decoded.get('portnum')

    print(f"\n\n====== {port} <<< {sender} >>> {to}")
    if port == 'SIMULATOR_APP':
        ins = decoded.get('simulator').get('portnum')
        print(f'Simulator Packet {ins}')
        pack = decoded.get('simulator')

        RADIO_PACKETS_PORT.labels(ins).inc()
        RADIO_PACKETS_SENDER.labels(sender).inc()

    else:
        pack = decoded

        if sender in interface.nodes:
            print(f"FROM: {interface.nodes[sender]['user']['shortName']} {interface.nodes[sender]['user']['longName']}")

        if 'X%s' % sender not in DATA:
            DATA['X%s' % sender] = {}


        if port == 'POSITION_APP':
            print('Updated Position for %s' % sender)
            DATA['X%s' % sender]['position'] = pack.get('position')
            pprint.pprint(pack.get('position'))

        if port == 'TELEMETRY_APP':
            print('Updated Telemetry for %s' % sender)
            DATA['X%s' % sender]['telemetry'] = pack.get('telemetry')
            pprint.pprint(pack.get('telemetry'))

        if port == 'NODEINFO_APP':
            print('Updated Nodeinfo for %s' % sender)
            DATA['X%s' % sender]['user'] = pack.get('user')
            pprint.pprint(pack.get('user'))

        if port == 'TEXTMESSAGE_APP':
            print('TEXT MESSAGE: %s' % pack)
            pprint.pprint(pack)

            #if 'X%s' % sender in DATA:
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


