# Prometheus Meshtastic Exporter

***WORK IN PROGRESS***

First cut of a prometheus exporter for meshtastic nodes.

This has only been tested against the Linux Native meshtastic build running in simulator mode connected to the global MQTT server (using the msh/ANZ root) and tracks those simulator packets as "radio" packets.

The exporter expects to find a meshtastic simulator on localhost, instructions for setting up the Linux Native build can be found at [https://meshtastic.org/docs/software/linux-native/](https://meshtastic.org/docs/software/linux-native/).

## Current Metrics

The exporter currently splits packets into "radio" (packets coming from SIMULATOR\_APP port) and "local" (packets to/from the node in question, including packets to ^all).

# Get Started

To get up and running; create a python virtual environment and run:

```pip install -r requirements.txt```

To start the scraper:

```python3 mon.py```

# To Do

* Docker container
* Message logging

