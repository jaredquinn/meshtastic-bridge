
from prometheus_client import start_http_server, Summary, Counter, Gauge, Info
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

UPDATE_SECONDS = 30

METRICS = {
  'SIM_PACKETS_PORT': Counter('sim_packets_app', 'Sim Packets by App', ['portnum']),
  'SIM_PACKETS_SENDER': Counter('sim_packets_sender', 'Sim Packets by Sender', ['sender']),
  'LOCAL_PACKETS_PORT': Counter('local_packets_app', 'Local Packets by App', ['portnum']),
  'LOCAL_PACKETS_SENDER': Counter('local_packets_sender', 'Local Packets by Sender', ['sender']),

  'NODE_CH_UTILISATION': Gauge('node_channel_util', 'Node Telemetry Channel Utilisation', ['sender']),
  'NODE_AIRTX_UTILISATION': Gauge('node_airtx_util', 'Node Telemetry Air TX Utilisation', ['sender']),
  'NODE_COUNT': Gauge('node_count', 'Number of Nodes seen in last 10 minutes'),
  #'NODE_SHORTNAME': Info('node_shortname', 'Node Information', ['sender']),
  #'NODE_LONGNAME': Info('node_longname', 'Node Longname', ['sender']),
  #'NODE_MAC': Info('node_macaddress', 'Node MAC Address', ['sender']),
  #'NODE_HARDWARE': Info('node_hardware', 'Node Hardware', ['sender']),
  #'NODE_ROLE': Info('node_role', 'Node Role', ['sender']),
}

def getTimeAgo(ts):
    """Format how long ago have we heard from this node (aka timeago)."""
    return datetime.now() - datetime.fromtimestamp(ts) if ts else None

class Prometheus_Plugin:

    def __init__(self):
        self._count = 0

    def handle_TELEMETRY_APP(self, sender, fullpacket, interface=None):
        packet = fullpacket.get('decoded')
        telem = packet.get('telemetry', {})
        if 'deviceMetrics' in telem:
            logger.debug(f'Updating Telemetry Mertics')
            if 'airUtilTx' in telem['deviceMetrics']:
                METRICS['NODE_AIRTX_UTILISATION'].labels(sender).set( telem['deviceMetrics'].get('airUtilTx',0) )
            if 'channelUtilization' in telem['deviceMetrics']:
                METRICS['NODE_CH_UTILISATION'].labels(sender).set( telem['deviceMetrics'].get('channelUtilization',0) )

    def update_nodecount(self, interface=None):
        logger.debug('Updating Node Count')
        nodes = []
        for node in interface.nodes.values():
            r = {}
            r['user'] = node.get('user')
            seconds = getTimeAgo(node.get("lastHeard"))
            if seconds is not None:
                if seconds.total_seconds() < 600:
                    r['since'] = seconds
                    nodes.append(node)

        logger.info("%d total, %d active" % (len(interface.nodes.values()), len(nodes)))
        METRICS['NODE_COUNT'].set(len(nodes))

    def count_packets(self, prefix, sender, port, interface=None):
        logger.debug('Updating Packet Counts')
        METRICS[f'{prefix}_PACKETS_PORT'].labels(port).inc()
        METRICS[f'{prefix}_PACKETS_SENDER'].labels(sender).inc()

    def start(self, interface=None):
        logger.info('Starting Prometheus Server')
        start_http_server(8000)

    def loop(self, interface=None):
        self._count = self._count + 1
        if self._count > UPDATE_SECONDS:
            self.update_nodecount(interface)
            self._count = 0

