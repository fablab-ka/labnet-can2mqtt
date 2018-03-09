# labnet-can2mqtt
Maps CAN to MQTT

This software is to be installed on the LabNet Bridge. It translates incoming CAN messages and publishes them in the configured MQTT bus. Also it listens for MQTT messages on the configured Channel and transmits them over the CAN interface. 


## Setup

* clone onto an raspberry pi (or similar) that is connected to the CAN interface 
* pip install -r requirements.txt
* Edit the config.py


## Configuration 

* mqtt_broker - the IP of the mqtt broker
* mqtt_broker_port - the port that is configured for the mqtt broker (usually 1883 or 8883)
* mqtt_client_id - the client id of this bridge unit
* mqtt_topic_template - the template of the topic the bridge should publish its messages on.
* canbus_interface - the name of the CAN interface that should be used
* canbus_type - the type of the CAN interface (e.g. socketcan) 
