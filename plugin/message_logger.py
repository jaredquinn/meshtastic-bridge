
import logging
import datetime

logger = logging.getLogger(__name__)

class MessageLogger_Plugin:

    def __init__(self, interface):
        self._interface = interface
        self.MESSAGE_LOG = open('messages.txt', 'a')
        print('Message Logger Plugin Loaded.  Writing to messages.txt')

    def handle_TEXT_MESSAGE_APP(self, sender, packet):
        payload = packet.get('payload', '')
        now = str(datetime.datetime.now().isoformat())
        print(f'Logger: Text Message Packet: {packet}')
        self.MESSAGE_LOG.write("%-28s %-7s %-4s: %s\n" % (
            now, 
            sender, 
            self._interface.nodes[sender]['user']['shortName'], 
            payload.decode('utf-8')))
        self.MESSAGE_LOG.flush()




