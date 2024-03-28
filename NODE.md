# Linux Native Node

A guide for building Linux Native Nodes.


## Building Linux Native for Docker

Checkout the source and checkout the version you want to build:

```
git clone https://github.com/meshtastic/firmware.git
cd firmware
checkout v2.2.9.47301a5
```

Copy the Dockerfile.node file from this to the firmware directory;
it has changes and updates from the release file, which currently 
*only* builds the development release from master branch.

The Dockerfile.node file in this repository uses the currently 
checked out code to build the image, and therefore can be used 
against any recent version.

Some older versions have known issues with some components;

To build:

```
docker build -t meshtastic:v2.2.9 -f Dockerfile.node .
```

Where -t is the name to give the container image you are creating.

To run the image:

```
docker run -d \
    -p 4403:4403 \
    --name meshtastic_mon \
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

