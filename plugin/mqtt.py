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


import paho.mqtt.client as mqtt
import logging
import json
import os

__PLUGIN_NAME__ = 'mqtt'

from meshtastic import telemetry_pb2, portnums_pb2 

logger = logging.getLogger(__name__)

LOCATION_SOURCE = os.environ.get('MESH_LOCATION_SOURCE', None)

MQTT_HOST = os.environ.get('MQTT_HOST', None)
MQTT_PORT = os.environ.get('MQTT_PORT', 1883)

UPDATE_SECONDS = os.environ.get('MQTT_TELEMETRY_UPDATE', 300)

TOPIC_TEXT_MESSAGE_PUBLISH = "meshtastic/default/textmessage"
TOPIC_TEXT_MESSAGE_SEND = "meshtastic/default/sendtext"

TOPIC_MAP={
  'statestream/sensor/gps/latitude': 'latitude',
  'statestream/sensor/gps/longitude': 'longitude',
  'statestream/sensor/gps/elevation': 'elevation',
  'wxpub/inside_barometer/state': 'pressure',
  'rtl_433/miranda/devices/Holman-WS5029/60120/temperature_C': 'temperature',
  'rtl_433/miranda/devices/Holman-WS5029/60120/humidity': 'humidity'
}


class MQTT_Plugin:

    def __init__(self):
        self.DATA = {}
        self._count = 0

        for k,v in TOPIC_MAP.items():
           self.DATA[v] = 0

        if MQTT_HOST is None:
            logger.info("No MQTT_HOST Specified.  MQTT Plugin is inactive.")
            return

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.on_connect = self.on_mqtt_connect
        self._client.on_message = self.on_mqtt_message
        self._interface = None
        #self._client.enable_logger(logger)

    def handle_TEXT_MESSAGE_APP(self, sender, fullpacket, interface=None):
        if MQTT_HOST is None:
            return

        packet = fullpacket.get('decoded', {})
        logger.info(f'Text Message Packet: {packet}')
        payload = packet.get('payload', '')
        data = { 'message': payload.decode('utf-8') }
        channel = fullpacket.get('channel', 'default')
        if sender in interface.nodes:
            data['longname'] = interface.nodes[sender].get('longName', "")
            data['shortname'] = interface.nodes[sender].get('shortName', "")
        self._client.publish(f"{TOPIC_TEXT_MESSAGE_PUBLISH}/{channel}", json.dumps(data))

    def on_mqtt_connect(self, client, userdata, flags, reason_code, properties):
        logger.info(f"Connected MQTT with result code {reason_code}")
        logger.info(f"Subscribing to {TOPIC_TEXT_MESSAGE_SEND}")
        client.subscribe(TOPIC_TEXT_MESSAGE_SEND)
        for k,v in TOPIC_MAP.items():
          logger.info(f"Subscribing to {k}")
          client.subscribe(k)

    def on_mqtt_message(self, client, userdata, msg):

        if msg.topic == TOPIC_TEXT_MESSAGE_SEND:
            logger.debug(f"Sending message to default channel {msg.payload}")
            self._interface.sendText(msg.payload.decode('utf-8'))
        else:
            k = TOPIC_MAP[msg.topic]
            v = msg.payload.decode('utf-8')
            if v == '"n/a"':
                return
            self.DATA[k] = v
            logger.debug(self.DATA)

    def sendTelemetry(self, interface=None):
        if MQTT_HOST is None:
            return

        failed = False
        for k,v in self.DATA.items():
            if v == None:
                logger.error(f"Incompete Dataset Detected")
                failed = True

        logger.info('SENDING TELEMETRY')
        data = telemetry_pb2.Telemetry(
            environment_metrics = telemetry_pb2.EnvironmentMetrics(
                temperature=float(self.DATA.get('temperature')),
                relative_humidity=int(self.DATA.get('humidity')),
                barometric_pressure=float(self.DATA.get('pressure')),
            )
        )
        logger.info(data)

        if LOCATION_SOURCE == 'mqtt':
            try:
                res = interface.sendData(data, 
                   destinationId='^all', 
                   portNum=portnums_pb2.TELEMETRY_APP, 
                   channelIndex=0)
                #logger.debug(res)
                res = interface.sendPosition(
                   latitude=float(self.DATA.get('latitude')), 
                   longitude=float(self.DATA.get('longitude')), 
                   altitude=float(self.DATA.get('elevation')),
                )
                #logger.debug(res)
            except Exception as a:
                logger.error(f'Exception: {a}')

    def start(self, interface=None):
        if MQTT_HOST is not None:
            logger.debug(f'Connecting to MQTT Broker {MQTT_HOST}')
            self._client.connect(MQTT_HOST, MQTT_PORT, 120)
            logger.debug('Starting MQTT Loop')
            self._client.loop_start()

        self._interface = interface

    def loop(self, interface=None):
        if MQTT_HOST is None:
            return

        if UPDATE_SECONDS != 0:
            self._count = self._count + 1
            if self._count > int(UPDATE_SECONDS):
                logger.debug('**minuteman*')
                self.sendTelemetry(interface)
                self._count = 0



