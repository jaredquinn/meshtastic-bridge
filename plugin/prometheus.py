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
PROMETHEUS_UPDATE_SECONDS = 10

METRICS = {
  'SIM_PACKETS_PORT': Counter('sim_packets_app', 'Sim Packets by App', ['portnum']),
  'SIM_PACKETS_SENDER': Counter('sim_packets_sender', 'Sim Packets by Sender', ['sender']),
  'LOCAL_PACKETS_PORT': Counter('local_packets_app', 'Local Packets by App', ['portnum']),
  'LOCAL_PACKETS_SENDER': Counter('local_packets_sender', 'Local Packets by Sender', ['sender']),

  'NODE_CH_UTILISATION': Gauge('node_channel_util', 'Node Telemetry Channel Utilisation', ['sender']),
  'NODE_AIRTX_UTILISATION': Gauge('node_airtx_util', 'Node Telemetry Air TX Utilisation', ['sender']),

  'NODE_COUNT': Gauge('node_count', 'Number of Nodes seen in last 5 minutes (lastseen in Meshtastic)'),
  'NODE_COUNT_2HR': Gauge('node_count_2h', 'Number of Nodes seen in last 2 hours (lastseen in Meshtastic)'),
  'NODE_SEEN': Gauge('node_seen', 'Number of Nodes that we saw traffic from in last 5 minutes'),
  'NODE_SEEN_2HR': Gauge('node_seen_2h', 'Number of Nodes that we saw traffic from in last 2 hours'),
}


def getTimeAgo(ts):
    """Format how long ago have we heard from this node (aka timeago)."""
    return datetime.now() - datetime.fromtimestamp(ts) if ts else None

class Prometheus_Plugin:

    def __init__(self):
        self.lastseen = {}
        self._count = 0
        self.active = False

        if PROMETHEUS_PORT is None:
            logger.warn('No PROMETHEUS_PORT specified.  Not collecting metrics.')


    def handle_TELEMETRY_APP(self, sender, fullpacket, interface=None):
        if not self.active: return

        packet = fullpacket.get('decoded')
        telem = packet.get('telemetry', {})
        if 'deviceMetrics' in telem:
            logger.debug(f'Updating Telemetry Mertics')
            if 'airUtilTx' in telem['deviceMetrics']:
                METRICS['NODE_AIRTX_UTILISATION'].labels(sender).set( telem['deviceMetrics'].get('airUtilTx',0) )
            if 'channelUtilization' in telem['deviceMetrics']:
                METRICS['NODE_CH_UTILISATION'].labels(sender).set( telem['deviceMetrics'].get('channelUtilization',0) )

    def update_nodecount(self, interface=None):
        """
        Update nodecount using the meshtastic nodedb lastheard time
        """
        if not self.active: return

        logger.debug('Updating Node Count')
        count2h = count = 0
        for node in interface.nodes.values():
            #print(node)
            seconds = getTimeAgo(node.get("lastHeard"))
            if seconds is not None:
                if seconds.total_seconds() < 600:
                    count = count + 1
                if seconds.total_seconds() < 7200:
                    count2h = count2h + 1

        METRICS['NODE_COUNT'].set(count)
        METRICS['NODE_COUNT_2HR'].set(count2h)
        logger.info("Meshtastic (node_count): %d total, %d active (5m) %d active (2h)" % \
                (len(interface.nodes.values()), count, count2h))

    def update_nodecount_internal(self, interface=None):
        """
        Update nodecount using the internal lastheard time
        """
        if not self.active: return

        total = nodecount = nc2h = 0
        for n,v in self.lastseen.items():
            delta = datetime.now() - v 
            if delta.total_seconds() < 600:
                nodecount = nodecount + 1
            if delta.total_seconds() < 7200:
                nc2h = nc2h + 1
            total = total + 1

        METRICS['NODE_SEEN'].set(nodecount)
        logger.info("Packets Seen (node_seen): %d total, %d active (5m) %d active (2h)" % \
                (total, nodecount, nc2h))


    def count_packets(self, prefix, sender, port, interface=None):
        if not self.active: return

        logger.debug('Updating Packet Counts')
        METRICS[f'{prefix}_PACKETS_PORT'].labels(port).inc()
        METRICS[f'{prefix}_PACKETS_SENDER'].labels(sender).inc()

        self.lastseen[sender] = datetime.now()

    def start(self, interface=None):

        if PROMETHEUS_PORT is not None:
            logger.info(f'Starting Prometheus Server.  Listening on {PROMETHEUS_PORT}')
            start_http_server(int(PROMETHEUS_PORT))

            for node in interface.nodes.values():
                user = node.get('user', {})
                lh = node.get('lastHeard')
                if lh:
                    self.lastseen[user.get('id')] = datetime.fromtimestamp(node.get('lastHeard'))

            self.active = True

    def loop(self, interface=None):
        if not self.active: return

        self._count = self._count + 1
        if self._count >= PROMETHEUS_UPDATE_SECONDS:
            self.update_nodecount(interface)
            self.update_nodecount_internal(interface)
            self._count = 0


