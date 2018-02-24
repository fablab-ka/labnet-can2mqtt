import sys
import can
import logging
import paho.mqtt.client as mqtt

from config import Config

def onMqttMessage(client, userdata, mqttMessage):
    pass # todo send can message


def onCanMessage(mqttClient, canMessage):
    pass # todo sendMqttMessage(mqttClient, canMessage)

def sendCanMessage(bus, id, msg):
    bus.send(can.Message(extended_id=False, arbitration_id=id, data=msg))

def sendMqttMessage(mqttClient, message):
    try:
        topic = Config.mqtt_topic_base + "04f01031"  # todo translate message to topic
        payload = "test"  # todo translate message to payload
        result = mqttClient.publish(topic, payload)
        if not (result[0] == mqtt.MQTT_ERR_SUCCESS):
            logging.error("Error publishing message \"%s\" to topic \"%s\". Return code %s: %s" % (
                topic, payload, str(result[0]), mqtt.error_string(result[0]
            )))
    except BaseException as e:
        logging.error("Error relaying message {%s}. Error: {%s}" % (message, e))


def init():
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT)

    logging.info("Starting CAN bus")
    if not Config.canbus_type:
        logging.error("No can interface specified. Valid interfaces are: %s" %
                      can.interface.can.VALID_INTERFACES)
        sys.exit(1)

    try:
        bus = can.interface.Bus(Config.canbus_interface, bustype=Config.canbus_type)
        canBuffer = can.BufferedReader()
        notifier = can.Notifier(bus, [canBuffer], timeout=0.1)
    except BaseException as e:
        logging.error("CAN bus error: %s" % e)
        sys.exit(1)

    logging.info("Starting MQTT")

    mqttClient = mqtt.Client(client_id=Config.mqtt_client_id,
                         protocol=mqtt.MQTTv31)
    mqttClient.on_message = onMqttMessage

    try:
        mqtt_errno = mqttClient.connect(Config.mqtt_broker, Config.mqtt_broker_port, 60)
        if mqtt_errno != 0:
            raise Exception(mqtt.error_string(mqtt_errno))

        mqttClient.loop_start()
    except BaseException as e:
        logging.error("MQTT error: %s" % e)
        bus.shutdown()
        notifier.stop()

    logging.info("Adding MQTT subscriptions")
    try:
        mqttClient.subscribe(Config.mqtt_topic_base)
    except BaseException as e:
        logging.error("Error adding subscribtion \"%s\": %s" %
                      (Config.mqtt_topic_base, e))

    logging.info("Starting main loop")
    try:
        while True:
            message = canBuffer.get_message()
            if message is not None:
                onCanMessage(mqttClient, message)
    except KeyboardInterrupt:
        bus.shutdown()
        notifier.stop()
        mqttClient.loop_stop()
        mqttClient.disconnect()

if __name__ == '__main__':
    init()
