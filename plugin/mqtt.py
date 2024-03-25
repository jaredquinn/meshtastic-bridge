
import paho.mqtt.client as mqtt
import logging

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

    def __init__(self, interface):
        print('MQTT Telemetry Plugin Initialized')
        self._interface = interface
        self.DATA = {}

        for k,v in TOPIC_MAP.items():
           self.DATA[v] = 0

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.on_connect = self.on_mqtt_connect
        self._client.on_message = self.on_mqtt_message
        self._count = 0

    def handle_TEXT_MESSAGE_APP(self, sender, packet):
        payload = packet.get('payload', '')
        print(f'MQTT: Text Message Packet: {packet}')
        self._client.publish(TOPIC_TEXT_MESSAGE_PUBLISH, payload)


    def on_mqtt_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connected MQTT Telemetry with result code {reason_code}")
        print(f"Subscribing to {TOPIC_TEXT_MESSAGE_SEND}")
        client.subscribe(TOPIC_TEXT_MESSAGE_SEND)
        for k,v in TOPIC_MAP.items():
          print(f"Subscribing to {k}")
          client.subscribe(k)

    def on_mqtt_message(self, client, userdata, msg):

        if msg.topic == TOPIC_TEXT_MESSAGE_SEND:
            print(f"Sending message to default channel {msg.payload}")
            self._interface.sendText(msg.payload.decode('utf-8'))
        else:
            k = TOPIC_MAP[msg.topic]
            v = msg.payload.decode('utf-8')
            if v == '"n/a"':
                return
            self.DATA[k] = v
            print(self.DATA)

    def on_mesh_response(self, p=None):
        print('==RESPONSE==')
        print(p)


    def sendTelemetry(self):
        failed = False
        for k,v in self.DATA.items():
            if v == None:
                print(f"Incompete Dataset Detected")
                failed = True

        print('SENDING TELEMETRY')
        data = telemetry_pb2.Telemetry(
            environment_metrics = telemetry_pb2.EnvironmentMetrics(
                temperature=float(self.DATA.get('temperature')),
                relative_humidity=int(self.DATA.get('humidity')),
                barometric_pressure=float(self.DATA.get('pressure')),
            )
        )
        try:
            print(data)
            res = self._interface.sendData(data, 
               destinationId='^all', 
               portNum=portnums_pb2.TELEMETRY_APP, 
               channelIndex=0, onResponse=self.on_mesh_response)
            print(res)
            res = self._interface.sendPosition(
               latitude=float(self.DATA.get('latitude')), 
               longitude=float(self.DATA.get('longitude')), 
               altitude=float(self.DATA.get('elevation')),
            )
            print(res)
        except Exception as a:
            print('Exception', a)

    def start(self):
        print('Starting MQTT Plugin')
        self._client.connect(MQTT_HOST, 1883, 60)
        print('Starting MQTT Loop')
        self._client.loop_start()

    def loop(self):
        self._count = self._count + 1
        if self._count > UPDATE_SECONDS:
            print('Minuteman')
            self.sendTelemetry()
            self._count = 0



