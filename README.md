# labnet-can2mqtt
Maps CAN to MQTT

This software is to be installed on the LabNet Bridge. It translates incoming CAN messages and publishes them in the configured MQTT bus. Also it listens for MQTT messages on the configured Channel and transmits them over the CAN interface.


## Setup

* clone onto an raspberry pi (or similar) that is connected to the CAN interface
* `sudo ./install.sh`


## Configuration

* mqtt_broker - the IP of the mqtt broker
* mqtt_broker_port - the port that is configured for the mqtt broker (usually 1883 or 8883)
* mqtt_client_id - the client id of this bridge unit
* mqtt_topic_template - the template of the topic the bridge should publish its messages on.
* mqtt_topic_iterator1_max - the max value of the first iterator inside the template
* mqtt_topic_iterator2_max - the max value of the second iterator inside the template
* default_target_power_hub - the id of the default target power hub (not mapped to MQTT)
* mqtt_cmd_topic_iterators_regex - the regex to find the iterators inside the mqtt topic (see mqtt_topic_template)
* canbus_interface - the name of the CAN interface that should be used
* canbus_type - the type of the CAN interface (e.g. socketcan or virtual to test)

## Debugging

### without CAN hardware

set the canbus_type to "virtual" in the config.py

### without an MQTT server

execute the following command on shell with installed nodejs
```npx mosca -v | npx pino```

then set localhost as mqtt_broker in the config.py