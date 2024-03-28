# 
# This file is part of the meshtastic monitoring bridge distribution
# (https://github.com/jaredquinn/meshtastic-bridge).
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


import logging
import datetime
import os

__PLUGIN_NAME__ = 'msglog'

logger = logging.getLogger(__name__)


MESSAGE_LOG=os.environ.get('MESH_MESSAGE_LOG', "messages.txt")

class MessageLogger_Plugin:

    def __init__(self):
        self.MESSAGE_LOG = open(MESSAGE_LOG, 'a')
        logger.info('Message Logger Plugin Loaded.  Writing to messages.txt')

    def handle_TEXT_MESSAGE_APP(self, sender, fullpacket, interface=None):

        packet = fullpacket.get('decoded', {})

        channel = fullpacket.get('channel', 0)
        sender = fullpacket.get('fromId') 
        short = '????'

        payload = packet.get('payload', '')
        now = str(datetime.datetime.now().isoformat())
        logger.info(f'Text Message Packet: {packet}')

        if sender in interface.nodes:
            short = interface.nodes[sender].get('user', {}).get('shortName')

        self.MESSAGE_LOG.write("%-19s %1d %-7s %-4s: %s\n" % (
            now, 
            channel,
            sender, 
            short,
            payload.decode('utf-8')))
        self.MESSAGE_LOG.flush()




