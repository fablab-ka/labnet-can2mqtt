import sys
import can
import logging
import paho.mqtt.client as mqtt

from config import Config


def on_mqtt_message(client, userdata, mqtt_message):
    logging.debug("received MQTT message")
    pass # todo send can message

def on_can_message(mqtt_client, can_message):
    logging.debug("received CAN message")
    arbitration_id = can_message.arbitration_id
    data = can_message.data

    print(format(arbitration_id, '#10x'))
    
    message_type = arbitration_id & 0xFF000000

    if message_type == 0x01:
        logging.debug("Message Type: local event")
        handle_local_event_message(mqtt_client, arbitration_id, data)
    else:
        logging.debug("Unknown Message Type")


def handle_local_event_message(mqtt_client, arbitration_id, data):
    node_type = arbitration_id & 0x00F00000

    if node_type == 0x0: # Bridge
        logging.debug("Node Type: Bridge")
    elif node_type == 0x1:  # Basis
        logging.debug("Node Type: Basis")
    elif node_type == 0xF:  # Power-Hub
        logging.debug("Node Type: Power-Hub")
        handle_power_hub_message(mqtt_client, arbitration_id, data)
    else:
        logging.debug("Unknown Node Type")


def handle_power_hub_message(mqtt_client, arbitration_id, data):
    node_id  = arbitration_id & 0x000FF000
    event_id = arbitration_id & 0x00000FFF
    steckdosen_id = node_id * (event_id - 0x30)

    min_amp = data & 0xFF00000000000000
    max_amp = data & 0x00FF000000000000

    logging.debug("min amp " + min_amp)
    logging.debug("max amp " + max_amp)
    
    dose = []
    dose.append(data & 0x0000FF0000000000)
    dose.append(data & 0x000000FF00000000)
    dose.append(data & 0x00000000FF000000)
    dose.append(data & 0x0000000000FF0000)
    dose.append(data & 0x000000000000FF00)
    dose.append(data & 0x00000000000000FF)

    for i in range(6):
        topic = create_mqtt_stat_topic(steckdosen_id, i+1)
        payload = dose[i]
        send_mqtt_message(mqtt_client, topic, payload)


def create_mqtt_stat_topic(steckdosen_id, dosen_id):
    return Config.mqtt_topic_template % [steckdosen_id, dosen_id, "/stat/power"]

def send_can_message(bus, id, msg):
    bus.send(can.Message(extended_id=False, arbitration_id=id, data=msg))

def send_mqtt_message(mqtt_client, topic, payload):
    try:
        result = mqtt_client.publish(topic, payload)
        if not (result[0] == mqtt.MQTT_ERR_SUCCESS):
            logging.error("Error publishing message \"%s\" to topic \"%s\". Return code %s: %s" % (
                topic, payload, str(result[0]), mqtt.error_string(result[0]
            )))
    except BaseException as e:
        logging.error("Error relaying message {%s} '%s'. Error: {%s}" % (topic, payload, e))


def init():
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    logging.info("Starting CAN bus")
    if not Config.canbus_type:
        logging.error("No can interface specified. Valid interfaces are: %s" %
                      can.interface.can.VALID_INTERFACES)
        sys.exit(1)

    try:
        bus = can.interface.Bus(Config.canbus_interface, bustype=Config.canbus_type)
        can_buffer = can.BufferedReader()
        notifier = can.Notifier(bus, [can_buffer], timeout=0.1)
    except BaseException as e:
        logging.error("CAN bus error: %s" % e)
        sys.exit(1)

    logging.info("Starting MQTT")

    mqtt_client = mqtt.Client(client_id=Config.mqtt_client_id,
                         protocol=mqtt.MQTTv31)
    mqtt_client.on_message = on_mqtt_message

    try:
        mqtt_errno = mqtt_client.connect(Config.mqtt_broker, Config.mqtt_broker_port, 60)
        if mqtt_errno != 0:
            raise Exception(mqtt.error_string(mqtt_errno))

        mqtt_client.loop_start()
    except BaseException as e:
        logging.error("MQTT error: %s" % e)
        bus.shutdown()
        notifier.stop()

    logging.info("Adding MQTT subscriptions")
    try:
        mqtt_client.subscribe(Config.mqtt_topic_base)
    except BaseException as e:
        logging.error("Error adding subscribtion \"%s\": %s" %
                      (Config.mqtt_topic_base, e))

    logging.info("Starting main loop")
    try:
        while True:
            message = can_buffer.get_message()
            if message is not None:
                on_can_message(mqtt_client, message)
    except KeyboardInterrupt:
        bus.shutdown()
        notifier.stop()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

if __name__ == '__main__':
    init()
