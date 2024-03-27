# Prometheus Meshtastic Exporter

***WORK IN PROGRESS***

First cut of a prometheus exporter for meshtastic nodes.

This has only been tested against the Linux Native meshtastic build running in simulator mode connected to the global MQTT server (using the msh/ANZ root) and tracks those simulator packets as "radio" packets.

The exporter expects to find a meshtastic simulator on localhost, instructions for setting up the Linux Native build can be found at [https://meshtastic.org/docs/software/linux-native/](https://meshtastic.org/docs/software/linux-native/).

## Configuration

Configuration is currently entirely by environment variable; specifically designed
for use with Docker.

* MESHTASTIC\_HOST - Hostname or IP of Meshtastic Node (localhost)

Additional configuration can be specified for each plugin as specified in the relevant section.


## Plugin Architecture

As functionality expanded quickly a simple class based plugin system was adopted.

Current plugins:

* aprs - Publish node positions to APRS
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

#### Configuration

* PROMETHEUS\_PORT - Port to listen on for prometheus (8000).

### MQTT

See the plugin script for the topic to data mapping.
Telemetry and position are updated every UPDATE\_SECONDS seconds (as defined in script).

The MQTT Host can be set in MQTT\_HOST.

Additionally two other topics are used:

* TOPIC\_TEXT\_MESSAGE\_PUBLISH - A copy of the payload of each text message on the default channel will be published here.
* TOPIC\_TEXT\_MESSAGE\_SEND - Send a text message to the default channel with the contents of the MQTT message

#### Configuration

MQTT Plugin will not be activated if MQTT\_HOST is not specified

* MQTT\_HOST - Hostname or IP of the MQTT Broker to connect to (None)
* MQTT\_TELEMETRY\_UPDATE - Number of seconds between sending MQTT Telemetry Data (300)

### Message Logging

The script now also logs all TEXT\_MESSAGE\_APP payloads processed on local to messages.txt.

Channel number logging appears to be based on the sender's channel not the locally matched channel.  This is an API issue.

#### Configuration

* MESH\_MESSAGE\_LOG - Filepath to the messages.txt log file (messages.txt)

### APRS

Node positions can be exported to APRS via APRS-IS.  

#### Configuration

* APRS\_CALLSIGN - Callsign for logging into APRS-IS
* APRS\_PASSWORD - Password for logging into APRS-IS
* APRS\_SERVER - Server to connect to (rotate.aprs2.net)
* APRS\_PORT - Server port to connect to (14580)
* APRS\_TEXT - Text to append to APRS comment (MQTT,ANZ,Longfast)
* APRS\_LOCATION - Location data in APRS format to provide beacons (3353.28S/15111.86E)
* APRS\_BEACON - Beacon interval for master node (self) beacon 

The APRS plugin will not start without the CALLSIGN and PASSWORD provided

# Get Started

To get up and running; create a python virtual environment and run:

```pip install -r requirements.txt```

To start the scraper:

```python3 mon.py```

# To Do

* Docker container
* Configuration/Command Line Options

