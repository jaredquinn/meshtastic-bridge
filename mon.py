import datetime
import meshtastic
import meshtastic.tcp_interface
import json
import pprint
import logging
import time
import random

from prometheus_client import start_http_server, Summary, Counter, Gauge, Info

from pubsub import pub

logging.basicConfig()

logger = logging.getLogger(name="meshtastic.stat")
logger.setLevel(logging.DEBUG)

interface = meshtastic.tcp_interface.TCPInterface(hostname="localhost")

METRICS = {
  'SIM_PACKETS_PORT': Counter('sim_packets_app', 'Sim Packets by App', ['portnum']),
  'SIM_PACKETS_SENDER': Counter('sim_packets_sender', 'Sim Packets by Sender', ['sender']),
  'LOCAL_PACKETS_PORT': Counter('local_packets_app', 'Local Packets by App', ['portnum']),
  'LOCAL_PACKETS_SENDER': Counter('local_packets_sender', 'Local Packets by Sender', ['sender']),

  'NODE_CH_UTILISATION': Gauge('node_channel_util', 'Node Telemetry Channel Utilisation', ['sender']),
  'NODE_AIRTX_UTILISATION': Gauge('node_airtx_util', 'Node Telemetry Air TX Utilisation', ['sender']),
  #'NODE_SHORTNAME': Info('node_shortname', 'Node Information', ['sender']),
  #'NODE_LONGNAME': Info('node_longname', 'Node Longname', ['sender']),
  #'NODE_MAC': Info('node_macaddress', 'Node MAC Address', ['sender']),
  #'NODE_HARDWARE': Info('node_hardware', 'Node Hardware', ['sender']),
  #'NODE_ROLE': Info('node_role', 'Node Role', ['sender']),
}

MESSAGE_LOG = open('messages.txt', 'a')


def handle_TEXT_MESSAGE_APP(sender, message):
    now = str(datetime.datetime.now().isoformat())
    print(now)
    MESSAGE_LOG.write("%-28s %-7s %-4s: %s\n" % (now, sender, interface.nodes[sender]['user']['shortName'], message.decode('utf-8')))
    MESSAGE_LOG.flush()
    logger.debug(f'TEXT MESSAGE: {message}')


def handle_NODEINFO_APP(sender, user):
    logger.debug(f'NODEINFO_APP: Updated Nodeinfo for {user}')
    pass


def handle_TELEMETRY_APP(sender, telem):
    if 'deviceMetrics' in telem:
        logger.debug(f'TELEMETRY_APP: Updating Telemetry Mertics')
        if 'airUtilTx' in telem['deviceMetrics']:
            METRICS['NODE_AIRTX_UTILISATION'].labels(sender).set( telem['deviceMetrics'].get('airUtilTx',0) )
        if 'channelUtilization' in telem['deviceMetrics']:
            METRICS['NODE_CH_UTILISATION'].labels(sender).set( telem['deviceMetrics'].get('channelUtilization',0) )

def handle_POSITION_APP(sender, position):
    logger.debug(f"POSITION_APP: {position['longitude']}, {position['latitude']}")


def count_packets(prefix, sender, port):
    METRICS[f'{prefix}_PACKETS_PORT'].labels(port).inc()
    METRICS[f'{prefix}_PACKETS_SENDER'].labels(sender).inc()


def onConnection(interface, topic=pub.AUTO_TOPIC):
    nodeInfo = interface.getMyNodeInfo()
    logger.info(f"Connected to node: userId={nodeInfo['user']['id']} hwModel={nodeInfo['user']['hwModel']}")


def onReceive(packet, interface):
    sender = packet['fromId']
    to = packet.get('toId')
    decoded = packet.get('decoded')
    port = decoded.get('portnum')

    if port == 'SIMULATOR_APP':
        ins = decoded.get('simulator',{}).get('portnum')
        logger.info(f"SIMPKT: {ins} <<< {sender} >>> {to}")
        count_packets('SIM', sender, ins)

    else:
        logger.info(f"LCLPKT: {port} <<< {sender} >>> {to}")
        pack = decoded

        if sender in interface.nodes:
            logger.debug(f"FROM: {interface.nodes[sender]['user']['shortName']} {interface.nodes[sender]['user']['longName']}")

        if port == 'POSITION_APP':
            handle_POSITION_APP(sender, pack.get('position',{}))

        if port == 'TELEMETRY_APP':
            handle_TELEMETRY_APP(sender, pack.get('telemetry',{}))

        if port == 'NODEINFO_APP':
            handle_NODEINFO_APP(sender, pack.get('user', {}))

        if port == 'TEXT_MESSAGE_APP':
            handle_TEXT_MESSAGE_APP(sender, pack.get('payload', ''))

        count_packets('LOCAL', sender, port)

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


