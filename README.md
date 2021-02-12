# MAVLink GPS_STATUS Analyzer/ Live Display
This small script connects to a mavlink stream and displays the GPS_STATUS messages for each connected system.


## Installation
Clone this repository and install the python dependencies with `pip3 install -r requirements.txt`.


## Usage
PyMavlink supports many different types of connections, e.g.:
```shell
## For mavlink-router "normal" mode UDP endpoint
./mavlink_gnss_status.py -d udpin:$ip:$port

## For mavlink-router "eavesdropping" mode UDP endpoint
./mavlink_gnss_status.py -d udpout:$ip:$port

## For mavlink-router's TCP server (currently bug prone!)
./mavlink_gnss_status.py -d tcp:$ip:$port
```

Notes:
- Domain names also work instead of the IP address
- There is a bug in mavlink-router, when using it's TCP server port: https://github.com/mavlink-router/mavlink-router/issues/252.
