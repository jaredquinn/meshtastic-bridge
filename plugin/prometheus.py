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

from prometheus_client import start_http_server, Summary, Counter, Gauge, Info
from datetime import datetime
import os
import logging
logger = logging.getLogger(__name__)

__PLUGIN_NAME__ = 'prometheus'


PROMETHEUS_PORT=os.environ.get('PROMETHEUS_PORT', None)

UPDATE_SECONDS = 30

METRICS = {
  'SIM_PACKETS_PORT': Counter('sim_packets_app', 'Sim Packets by App', ['portnum']),
  'SIM_PACKETS_SENDER': Counter('sim_packets_sender', 'Sim Packets by Sender', ['sender']),
  'LOCAL_PACKETS_PORT': Counter('local_packets_app', 'Local Packets by App', ['portnum']),
  'LOCAL_PACKETS_SENDER': Counter('local_packets_sender', 'Local Packets by Sender', ['sender']),

  'NODE_CH_UTILISATION': Gauge('node_channel_util', 'Node Telemetry Channel Utilisation', ['sender']),
  'NODE_AIRTX_UTILISATION': Gauge('node_airtx_util', 'Node Telemetry Air TX Utilisation', ['sender']),
  'NODE_COUNT': Gauge('node_count', 'Number of Nodes seen in last 10 minutes'),
}

def getTimeAgo(ts):
    """Format how long ago have we heard from this node (aka timeago)."""
    return datetime.now() - datetime.fromtimestamp(ts) if ts else None

class Prometheus_Plugin:

    def __init__(self):
        if PROMETHEUS_PORT is None:
            logger.warn('No PROMETHEUS_PORT specified.  Not collecting metrics.')

        self._count = 0

    def handle_TELEMETRY_APP(self, sender, fullpacket, interface=None):
        if PROMETHEUS_PORT is None:
            return

        packet = fullpacket.get('decoded')
        telem = packet.get('telemetry', {})
        if 'deviceMetrics' in telem:
            logger.debug(f'Updating Telemetry Mertics')
            if 'airUtilTx' in telem['deviceMetrics']:
                METRICS['NODE_AIRTX_UTILISATION'].labels(sender).set( telem['deviceMetrics'].get('airUtilTx',0) )
            if 'channelUtilization' in telem['deviceMetrics']:
                METRICS['NODE_CH_UTILISATION'].labels(sender).set( telem['deviceMetrics'].get('channelUtilization',0) )

    def update_nodecount(self, interface=None):
        if PROMETHEUS_PORT is None:
            return

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
        if PROMETHEUS_PORT is None:
            return

        logger.debug('Updating Packet Counts')
        METRICS[f'{prefix}_PACKETS_PORT'].labels(port).inc()
        METRICS[f'{prefix}_PACKETS_SENDER'].labels(sender).inc()

    def start(self, interface=None):
        if PROMETHEUS_PORT is not None:
            logger.info(f'Starting Prometheus Server.  Listening on {PROMETHEUS_PORT}')
            start_http_server(int(PROMETHEUS_PORT))

    def loop(self, interface=None):
        if PROMETHEUS_PORT is None:
            return

        self._count = self._count + 1
        if self._count > UPDATE_SECONDS:
            self.update_nodecount(interface)
            self._count = 0

