# 
# Quick Bridge & Dirty to bring test data into a test node via MQTT
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

######################################################################
# This program is designed to perform a one-way proxy of MQTT traffic
# to a local MQTT server; primarily to provide test data during 
# development.  It can however also be used to monitor a mesh via MQTT
# without having a node appear in the nodelist.
# 
# Requires a self-hosted MQTT broker.
######################################################################

import paho.mqtt.client as mqtt
import logging
import json
import os
import time

MQTT_HOST = os.environ.get('MQTT_HOST', "10.10.1.100")
PROXY_TOPIC = os.environ.get('MQTT_PROXY_TOPIC', 'msh/ANZ/#')

_w = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="jqdev-0x10", protocol=mqtt.MQTTv5)
_l = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="jqdev-0x10")

# We use the default Meshtastic credentials for the global server as
# the broker to listen on
_l.username_pw_set(username="meshdev", password="large4cats")


def on_listen_message(client, userdata, msg):
    _w.publish(topic=msg.topic, payload=msg.payload)


def on_listen_connect(client, userdata, flags, reason_code, properties):
    print('Connected to Listener')
    client.subscribe(PROXY_TOPIC)

def on_write_connect(client, userdata, flags, reason_code, properties):
    print('Connected to Writer')

_l.on_connect = on_listen_connect
_l.on_message = on_listen_message
_w.on_connect = on_write_connect

_l.connect("mqtt.meshtastic.org", 1883, 60)
_w.connect(MQTT_HOST, 1883, 60)


print('Starting Loops')
_l.loop_start()
_w.loop_start()

print('Waiting for data')
while True:
    time.sleep(1)


