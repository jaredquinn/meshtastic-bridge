
import paho.mqtt.client as mqtt
import logging
import json

from meshtastic import telemetry_pb2, portnums_pb2 

logger = logging.getLogger(__name__)

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


UPDATE_SECONDS = 300
MQTT_HOST = '10.10.1.100'

class MQTT_Plugin:

    def __init__(self):
        logger.debug('MQTT Telemetry Plugin Initialized')
        self.DATA = {}

        for k,v in TOPIC_MAP.items():
           self.DATA[v] = 0

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.on_connect = self.on_mqtt_connect
        self._client.on_message = self.on_mqtt_message
        #self._client.enable_logger(logger)
        self._count = 0

    def handle_TEXT_MESSAGE_APP(self, sender, packet, interface=None):
        logger.info(f'MQTT: Text Message Packet: {packet}')
        payload = packet.get('payload', '')
        data = { 'message': payload.decode('utf-8') }
        if sender in interface.nodes:
            data['longname'] = interface.nodes[sender].get('longName', "")
            data['shortname'] = interface.nodes[sender].get('shortName', "")
        self._client.publish(TOPIC_TEXT_MESSAGE_PUBLISH, json.dumps(data))


    def on_mqtt_connect(self, client, userdata, flags, reason_code, properties):
        logger.info(f"Connected MQTT Telemetry with result code {reason_code}")
        logger.info(f"Subscribing to {TOPIC_TEXT_MESSAGE_SEND}")
        client.subscribe(TOPIC_TEXT_MESSAGE_SEND)
        for k,v in TOPIC_MAP.items():
          logger.info(f"Subscribing to {k}")
          client.subscribe(k)

    def on_mqtt_message(self, client, userdata, msg):

        if msg.topic == TOPIC_TEXT_MESSAGE_SEND:
            logger.debug(f"Sending message to default channel {msg.payload}")
            interface.sendText(msg.payload.decode('utf-8'))
        else:
            k = TOPIC_MAP[msg.topic]
            v = msg.payload.decode('utf-8')
            if v == '"n/a"':
                return
            self.DATA[k] = v
            logger.debug(self.DATA)

    def on_mesh_response(self, p=None):
        pass

    def sendTelemetry(self):
        failed = False
        for k,v in self.DATA.items():
            if v == None:
                logger.error(f"Incompete Dataset Detected")
                failed = True

        logger.debug('SENDING TELEMETRY')
        data = telemetry_pb2.Telemetry(
            environment_metrics = telemetry_pb2.EnvironmentMetrics(
                temperature=float(self.DATA.get('temperature')),
                relative_humidity=int(self.DATA.get('humidity')),
                barometric_pressure=float(self.DATA.get('pressure')),
            )
        )
        try:
            logger.debug(data)
            res = self._interface.sendData(data, 
               destinationId='^all', 
               portNum=portnums_pb2.TELEMETRY_APP, 
               channelIndex=0, onResponse=self.on_mesh_response)
            logger.debug(res)
            res = self._interface.sendPosition(
               latitude=float(self.DATA.get('latitude')), 
               longitude=float(self.DATA.get('longitude')), 
               altitude=float(self.DATA.get('elevation')),
            )
            logger.debug(res)
        except Exception as a:
            logger.error('Exception', a)

    def start(self, interface=None):
        logger.info('Starting MQTT Plugin')
        self._client.connect(MQTT_HOST, 1883, 60)
        logger.info('Starting MQTT Loop')
        self._client.loop_start()

    def loop(self, interface=None):
        self._count = self._count + 1
        if self._count > UPDATE_SECONDS:
            logger.debug('**minuteman*')
            self.sendTelemetry()
            self._count = 0



