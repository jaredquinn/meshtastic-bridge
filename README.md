# Prometheus Meshtastic Exporter

First cut of a prometheus exporter for meshtastic nodes.

This has only been tested against the Linux Native meshtastic build running in simulator mode connected to the global MQTT server (using the msh/ANZ root) and tracks those simulator packets as "radio" packets.

# WORK IN PROGRESS

To get up and running; create a python virtual environment and run:

```pip install -r requirements.txt```

To start the scraper:

```python3 mon.py```

# To Do

* Docker container
* Message logging

