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
* Additional PR raised to include libraries required by piwebserver at https://github.com/meshtastic/firmware/pull/3506.

The Dockerfile.node file in this changes this behaviour and builds from the current copy of the
code from the current working directory.    The file will be maintained here also for multiversion builds.

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
    -v /data/meshtastic/mon:/home/mesh/data \
    --log-opt mode=non-blocking --log-opt max-buffer-size=4m  \
    meshtastic:v2.2.9
```
## Webserver Support

Version v2.3.0 and later support the webserver on Linux Native builds and
the dockerfile here includes support for it.

Until PR 3506 is merged you will need to update your arch/portuino/portuino.ini file
before building the docker image to link against these libraries while building, scroll
to the bottom of the file and update build\_flags to include ssl, orcania and ulfius:

```
build_flags =
  ${arduino_base.build_flags}
  -fPIC
  -Isrc/platform/portduino
  -DRADIOLIB_EEPROM_UNSUPPORTED
  -DPORTDUINO_LINUX_HARDWARE
  -lbluetooth
  -lgpiod
  -lyaml-cpp
  -lssl
  -lorcania
  -lulfius
```

Build the container

```
docker build -t meshtastic:v2.3.2 -f Dockerfile.node .
```

Additionally the webserver requires a config.yaml to be loaded by meshtasticd 
and the static content mounted into the container at /web.  

Follow the instructions at https://github.com/meshtastic/web to build the web application.

Copy the bin/config-dist.yaml and edit the contents; it should include the following block:

```
Webserver:
  Port: 443
  RootPath: /web 
```

```
docker run -d \
    -p 4403:4403 \
    --name meshtastic-node \
    -v /data/meshtastic/mon/config.yaml:/home/mesh/config.yaml \
    -v /data/meshtastic/mon:/home/mesh/data \
    -v /data/meshtastic/web:/web \
    --log-opt mode=non-blocking --log-opt max-buffer-size=4m  \
    meshtastic:v2.3.2
```

Be sure to update the volume paths; the resulting container, paths to bind to are:

* /home/mesh/config.yaml (native build configuration file)
* /home/mesh/data (an empty directory for firmware filesystem data)
* /web (static web contents)


# Known Issues

## Webserver Support

Webserver on Linux Native build is entirely missing/unsupported prior to v2.3.0


## ctime error on src/gps/GPS.cpp

Edit the file and update the PORTDUINO block to include <ctime>

```
#ifdef ARCH_PORTDUINO
#include "meshUtils.h"
#include <ctime>
#endif
```

Observed in v2.2.9

