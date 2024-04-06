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

MQTT_UPDATE_SECONDS = os.environ.get('MQTT_TELEMETRY_UPDATE', 300)

MQTT_MESSAGE_ROOT = os.environ.get('MQTT_MESSAGE_ROOT', 'meshtastic/default')

TOPIC_TEXT_MESSAGE_PUBLISH = f"{MQTT_MESSAGE_ROOT/textmessage"
TOPIC_TEXT_MESSAGE_SEND = f"{MQTT_MESSAGE_ROOT}/sendtext"

TOPIC_MAP={
  'wxpub/inside_barometer/state': 'pressure',
  'rtl_433/miranda/devices/Holman-WS5029/60120/temperature_C': 'temperature',
  'rtl_433/miranda/devices/Holman-WS5029/60120/humidity': 'humidity'
}

LOCATION_MAP={
  'statestream/sensor/gps/latitude': 'latitude',
  'statestream/sensor/gps/longitude': 'longitude',
  'statestream/sensor/gps/elevation': 'elevation',
}

class MQTT_Plugin:

    def __init__(self):
        self.DATA = {}
        self._count = 0

        if LOCATION_SOURCE == 'mqtt':
            for k,v in LOCATION_MAP.items():
                TOPIC_MAP[k] = v

        for k,v in TOPIC_MAP.items():
           self.DATA[v] = 0

        if MQTT_HOST is None:
            logger.warning("No MQTT_HOST Specified.  MQTT Plugin is inactive.")
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
            logger.info(f'Updating internal telemetry {k}={v}')
            return

    def hasTelemetry(self):
        for k in ['temperature', 'humidity', 'pressure']:
            if self.DATA[k] == 0:
                logger.info(f'No data for {k}')
                return True
        return False

    def sendTelemetry(self, interface=None):
        if MQTT_HOST is None:
            return

        if not self.hasTelemetry():
            logger.info(f'No telemetry to send yet; waiting for data.')
            return

        data = telemetry_pb2.Telemetry(
            environment_metrics = telemetry_pb2.EnvironmentMetrics(
                temperature=float(self.DATA.get('temperature')),
                relative_humidity=int(self.DATA.get('humidity')),
                barometric_pressure=float(self.DATA.get('pressure')),
            )
        )

        logger.info(f'Sending TELEMETRY_APP Packet: {data}')

        res = interface.sendData(data, 
            destinationId='^all', 
            portNum=portnums_pb2.TELEMETRY_APP, 
            channelIndex=0)

    def sendPosition(self, interface):

        if LOCATION_SOURCE != 'mqtt':
            return

        lat = self.DATA.get('latitude')
        lon = self.DATA.get('longitude')
        alt = self.DATA.get('elevation')


        logger.info(f'Sending POSITION_APP Packet {lat} {lon} at {alt} elv')
        try:
            res = interface.sendPosition(
                latitude=float(d.get('latitude')), 
                longitude=float(d.get('longitude')), 
                altitude=float(d.get('elevation')),
            )

        except Exception as a:
            logger.critical(f'Exception: {a}')


    def start(self, interface=None):
        if MQTT_HOST is not None:
            logger.info(f'Connecting to MQTT Broker {MQTT_HOST}')
            self._client.connect(MQTT_HOST, MQTT_PORT, 120)

            logger.debug('Starting MQTT Loop')
            self._client.loop_start()

        self._interface = interface

    def loop(self, interface=None):
        if MQTT_HOST is None:
            return

        if MQTT_UPDATE_SECONDS != 0:
            self._count = self._count + 1
            if self._count >= int(MQTT_UPDATE_SECONDS):
                logger.debug('**minuteman*')
                self.sendTelemetry(interface)
                self.sendPosition(interface)
                self._count = 0


