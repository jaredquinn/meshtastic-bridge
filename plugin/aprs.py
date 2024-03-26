
import logging
import json
import aprslib
import os
from datetime import datetime, timezone
from meshtastic import telemetry_pb2, portnums_pb2 

# Your APRS-IS Callsign and Password should be set in these variables 
# to activate the APRS Bridge
logger = logging.getLogger(__name__)

APRS_CALLSIGN=os.environ.get('APRS_CALLSIGN')
APRS_PASSWORD=os.environ.get('APRS_PASSWORD')

APRS_HOST='rotate.aprs2.net'
APRS_PORT=14580

def integerToDMS(val, postfix):
    valDeg = int(val)
    valMin = (val-valDeg)*60
    valHth = int((valMin-int(valMin))*100)
    valMin = int(valMin)
    return "%d%02d.%02d%1s" % (valDeg, valMin, valHth, postfix)

def convertPosition(lat, lng):
    lngS = 'E' if lng > 0 else 'W'
    return integerToDMS(abs(lat), 'N' if lat > 0 else 'S') + '/' +  \
             integerToDMS(abs(lng), 'E' if lng > 0 else 'W')

class APRS_Plugin:

    def __init__(self):
        self._aprs = None
        logging.info('Plugin Initialized')

    def handle_POSITION_APP(self, sender, fullpacket, interface=None):

        pos = fullpacket.get('decoded',{}).get('position',{})
        sender = fullpacket.get('fromId')
        return self.process_position(sender,pos,interface)

    def process_position(self, sender, pos, interface):

        if APRS_CALLSIGN is None:
            return

        if 'latitudeI' not in pos or 'longitudeI' not in pos:
            logging.warn("Incomplete position in packet, not sending to APRS")
            return

        if sender is None:
            logging.warn("No Sender in this packet, not sending to APRS")
            return

        node = interface.nodes[sender]
        if not 'user' in node:
            logging.warn("No User in interfaces yet, not sending to APRS")
            return

        user = interface.nodes[sender].get('user')
        short = user.get('shortName')
        if short is None:
            logging.warn("Node has no shortname, not sending to APRS")

        long = user.get('longName')

        #logging.warn(f"Sender {sender}")
        #logging.warn(f"Node {node}")

        sender = sender.replace('!', 'M')
        lat = pos.get('latitude',0)
        lng = pos.get('longitude',0)
        logging.warn(f"Lat {lat} Long {lng}")
        pos = convertPosition(lat,lng)
        now = datetime.now(timezone.utc)
        ds = now.strftime("%d%H%Mz")
        #logging.warn(short)

        station = "MESH-%s" % short.replace(' ', '')
        MESSAGE=f"{station:<9}*{ds}{pos}nMestastic Node {short}/{long}, LongFast, ANZ"
        PACKET=f"{APRS_CALLSIGN}>APDW16,WIDE1-1:;{MESSAGE}"
        logging.warn(f"SENDING APRS: {PACKET}")
        self._aprs.sendall(PACKET)

    def start(self, interface=None):
        if APRS_CALLSIGN is None:
            logger.warn("Not setting up APRS, Variable not set")
            return

        self._aprs = aprslib.IS(APRS_CALLSIGN,
                      passwd=APRS_PASSWORD,
                      host=APRS_HOST,
                      port=APRS_PORT,
                      skip_login=False)

        self._aprs.connect(blocking=True)

        #now = datetime.now(timezone.utc)
        #ds = now.strftime("%d%H%Mz")
        #MESSAGE=f">{ds}I am a robot"
        #PACKET=f"{APRS_CALLSIGN}>APDW16,WIDE1-1:;{MESSAGE}"
        #logging.warn(f'Sending {PACKET}')
        #self._aprs.sendall(PACKET)

