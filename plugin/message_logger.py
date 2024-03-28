
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




