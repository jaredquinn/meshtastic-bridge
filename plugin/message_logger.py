
import logging
import datetime

logger = logging.getLogger(__name__)

class MessageLogger_Plugin:

    def __init__(self):
        self.MESSAGE_LOG = open('messages.txt', 'a')
        logger.info('Message Logger Plugin Loaded.  Writing to messages.txt')

    def handle_TEXT_MESSAGE_APP(self, sender, fullpacket, interface=None):

        packet = fullpacket.get('decoded', {})
        payload = packet.get('payload', '')

        now = str(datetime.datetime.now().isoformat())
        logger.info(f'Text Message Packet: {packet}')
        short = interface.nodes.get('sender', {}).get('user',{}).get('shortName', "~unknown~")

        self.MESSAGE_LOG.write("%-28s %-7s %-4s: %s\n" % (
            now, 
            sender, 
            short,
            payload.decode('utf-8')))
        self.MESSAGE_LOG.flush()




