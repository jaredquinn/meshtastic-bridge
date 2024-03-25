# Prometheus Meshtastic Exporter

***WORK IN PROGRESS***

First cut of a prometheus exporter for meshtastic nodes.

This has only been tested against the Linux Native meshtastic build running in simulator mode connected to the global MQTT server (using the msh/ANZ root) and tracks those simulator packets as "radio" packets.

The exporter expects to find a meshtastic simulator on localhost, instructions for setting up the Linux Native build can be found at [https://meshtastic.org/docs/software/linux-native/](https://meshtastic.org/docs/software/linux-native/).

## Plugin Architecture

As functionality expanded quickly a simple class based plugin system was adopted.

Current plugins:

* prometheus - Original Prometheus interface
* mqtt - Listen for telemetry & GPS data from MQTT topics to publish
* message\_logger - Log text message applications to message log

To enable/disable plugins please comment them from the PLUGINS array in mon.py

### Prometheus

#### Current Metrics

The exporter currently splits packets into "radio" (packets coming from SIMULATOR\_APP port) and "local" (packets to/from the node in question, including packets to ^all).

* sim\_packets\_app
* sim\_packets\_sender
* local\_packets\_app
* local\_packets\_sender
* node\_channel\_util
* node\_airtx\_util

### MQTT

See the plugin script for the topic to data mapping.
Telemetry and position are updated every UPDATE\_SECONDS seconds (as defined in script).

The MQTT Host can be set in MQTT\_HOST.

Additionally two other topics are used:

* TOPIC\_TEXT\_MESSAGE\_PUBLISH - A copy of the payload of each text message on the default channel will be published here.
* TOPIC\_TEXT\_MESSAGE\_SEND - Send a text message to the default channel with the contents of the MQTT message


### Message Logging

The script now also logs all TEXT\_MESSAGE\_APP payloads processed on local to messages.txt.

# Get Started

To get up and running; create a python virtual environment and run:

```pip install -r requirements.txt```

To start the scraper:

```python3 mon.py```

# To Do

* Docker container
* Configuration/Command Line Options

