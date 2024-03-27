
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
APRS_HOST=os.environ.get('APRS_SERVER', 'rotate.aprs2.net')
APRS_PORT=int(os.environ.get('APRS_PORT', "14580"))

APRS_TEXT=os.environ.get('APRS_TEXT', 'MQTT,ANZ,LongFast')
APRS_GATEWAY_LOCATION=os.environ.get('APRS_LOCATION', '3353.28S/15111.86E')

APRS_BEACON=int(os.environ.get('APRS_BEACON', "600"))

ROBOT_TEXT="I am a robot creating APRS Objects form Meshtastic position reports"


def integerToDMh(val, postfix):
    """
    Convert decimal long/lat to Deg Minutes Hundreths
    """
    valDeg = int(val)
    valMin = (val-valDeg)*60
    valHth = int((valMin-int(valMin))*100)
    valMin = int(valMin)
    return "%d%02d.%02d%1s" % (valDeg, valMin, valHth, postfix)

def convertPosition(lat, lng):
    """
    Convert decimal position to APRS format
    """
    lngS = 'E' if lng > 0 else 'W'
    return integerToDMh(abs(lat), 'N' if lat > 0 else 'S') + '/' +  \
             integerToDMh(abs(lng), 'E' if lng > 0 else 'W')

class APRS_Plugin:

    def __init__(self):
        self._rl = {}
        self._count = 0
        self._aprs = None
        self._enabled = False
        self._aprs = aprslib.IS(APRS_CALLSIGN,
                      passwd=APRS_PASSWORD,
                      host=APRS_HOST,
                      port=APRS_PORT,
                      skip_login=False)

        logger.info('Plugin Initialized')

    def handle_POSITION_APP(self, sender, fullpacket, interface=None):

        pos = fullpacket.get('decoded',{}).get('position',{})
        sender = fullpacket.get('fromId')
        return self.process_position(sender,pos,interface)

    def process_position(self, sender, pos, interface):

        if not self._enabled:
            logger.warn("Not sending packet due to no APRS-IS connection")
            return

        if APRS_CALLSIGN is None:
            return

        if 'latitudeI' not in pos or 'longitudeI' not in pos:
            logger.warn("Incomplete position in packet, not sending to APRS")
            return

        if sender is None:
            logger.warn("No Sender in this packet, not sending to APRS")
            return

        node = interface.nodes[sender]
        if not 'user' in node:
            logger.warn("No User in interfaces yet, not sending to APRS")
            return

        # user: {'id': '!da56df6c', 'longName': 'Bray Park 1', 'shortName': 'BPK1', 'macaddr': 'NLfaVt9s', 'hwModel': 'HELTEC_V3'}
        user = interface.nodes[sender].get('user')
        short = user.get('shortName')
        ky = sender.replace('!','')
        if short is None:
            logger.warn("Node has no shortname, not sending to APRS")

        long = user.get('longName')
        lat = pos.get('latitude',0)
        lng = pos.get('longitude',0)
        pos = convertPosition(lat,lng)
        logger.debug(f"Lat {lat} Long {lng} = {pos}")

        now = datetime.now(timezone.utc)
        ds = now.strftime("%d%H%Mz")
        hardware = user.get('hwModel')
        allowSend = True

        if ky in self._rl:
            lasttime = self._rl[ky]['last']
            lastpos = self._rl[ky]['position']
            print(self._rl[ky])

            if pos == pos and (now-lasttime).total_seconds() < 600:
                logger.warn("Setting allowSend=False as position hasnt changed and less than 600 seconds")
                allowSend = False

        if allowSend:
            station = "MESH-%s" % short.replace(' ', '')
            MESSAGE=f"{station:<9}*{ds}{pos}nMestastic Node {short}/{long}, {APRS_TEXT}. Device ID {sender} ({hardware})."
            PACKET=f"{APRS_CALLSIGN}>APDW16,WIDE1-1:;{MESSAGE}"
            logger.info(f"TX: {PACKET}")
            self._aprs.sendall(PACKET)
            self._rl[ky] = { 'last': now, 'position': pos }


    def start(self, interface=None):
        if APRS_CALLSIGN is None:
            logger.warn("Not setting up APRS, Variable not set")
            return


        self._aprs.connect(blocking=True)
        self._enabled = True

        nodeInfo = interface.getMyNodeInfo()
        logger.info(nodeInfo)
        self.beacon()

        # Set current status to I am a robot

        now = datetime.now(timezone.utc)
        ds = now.strftime("%d%H%Mz")
        MESSAGE=f">{ds}{ROBOT_TEXT}"
        PACKET=f"{APRS_CALLSIGN}>APDW16,WIDE1-1:{MESSAGE}"
        logging.warn(f'Sending {PACKET}')
        self._aprs.sendall(PACKET)


    def beacon(self):

        # @TODO: bacon on startup and regularly on timer
        now = datetime.now(timezone.utc)
        ds = now.strftime("%d%H%Mz")
        MESSAGE=f"!{APRS_GATEWAY_LOCATION}r/Meshtastic Gateway Node"
        PACKET=f"{APRS_CALLSIGN}>APDW16,WIDE1-1:{MESSAGE}"
        logger.warn(f'BEACON: {PACKET}')
        self._aprs.sendall(PACKET)

    def loop(self, interface=None):
        self._count = self._count + 1
        if self._count > APRS_BEACON:
            self.beacon()
            self._count = 0





