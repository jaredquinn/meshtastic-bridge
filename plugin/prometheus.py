
from prometheus_client import start_http_server, Summary, Counter, Gauge, Info

import logging
logger = logging.getLogger(__name__)


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

class Prometheus_Plugin:

    def __init__(self, interface):
        self._interface = interface

    def handle_TELEMETRY_APP(self, sender, telem):
        telem = packet.get('telemetry', {})
        if 'deviceMetrics' in telem:
            logger.debug(f'TELEMETRY_APP: Updating Telemetry Mertics')
            if 'airUtilTx' in telem['deviceMetrics']:
                METRICS['NODE_AIRTX_UTILISATION'].labels(sender).set( telem['deviceMetrics'].get('airUtilTx',0) )
            if 'channelUtilization' in telem['deviceMetrics']:
                METRICS['NODE_CH_UTILISATION'].labels(sender).set( telem['deviceMetrics'].get('channelUtilization',0) )

    def count_packets(self, prefix, sender, port):
        METRICS[f'{prefix}_PACKETS_PORT'].labels(port).inc()
        METRICS[f'{prefix}_PACKETS_SENDER'].labels(sender).inc()

    def start(self):
        print('Starting Prometheus Server')
        start_http_server(8000)

    def loop(self):
        pass



