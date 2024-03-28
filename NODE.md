# Linux Native Node

A guide for building Linux Native Nodes for Docker.


## Building Linux Native for Docker

Checkout the source and checkout the version you want to build:

```
git clone https://github.com/meshtastic/firmware.git
cd firmware
checkout v2.2.9.47301a5
```

Copy the [Dockerfile.node](Dockerfile.node) file from this repository to the firmware directory.

Current limitations in the Dockerfile contained within the firmware repository include:

* *only* building from the master branch pulled from github;  preventing local changes.
* Does not build on ARM architectures - I've raised a PR to fix this at https://github.com/meshtastic/firmware/pull/3500.

The Dockerfile.node file in this changes this behaviour and builds from the current copy of the
code from the current working directory.

Some older versions have known issues with some components see Caveats below.

## Building the image

Build a container image from your firmware directory by running docker build:

```
docker build -t meshtastic:v2.2.9 -f Dockerfile.node .
```

Where -t is the name to give the container image you are creating.

## Running the container

To start a container using your newly built image:

```
docker run -d \
    -p 4403:4403 \
    --name meshtastic-node \
    -v /data/meshtastic/mon/config.yaml:/etc/meshtasticd/config.yaml \
    -v /data/meshtastic/mon:/home/mesh/data \
    --log-opt mode=non-blocking --log-opt max-buffer-size=4m  \
    meshtastic:v2.2.9
```


## Known Issues

### ctime error on src/gps/GPS.cpp

Edit the file and update the PORTDUINO block to include <ctime>

```
#ifdef ARCH_PORTDUINO
#include "PortduinoGlue.h"
#include "meshUtils.h"
#include <ctime>
#endif
```

Observed in v2.2.9

