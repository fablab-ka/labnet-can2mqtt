import sys
import can
import logging
import struct
import re
import paho.mqtt.client as mqtt
from binascii import unhexlify, hexlify
from flask import Flask, render_template, send_from_directory
from werkzeug.serving import run_simple

from config import Config

httpApp = Flask(__name__)


@httpApp.route('/css/<path:path>')
def send_css(path):
    print path
    return send_from_directory('static', path)

@httpApp.route("/")
def hello():
    return render_template("index.html")

def on_mqtt_message(bus, client, userdata, mqtt_message):
    logging.debug("received MQTT message")

    #only for debugging, loopback
    #bus = can.interface.Bus(Config.canbus_interface, bustype=Config.canbus_type)

    match = re.search(Config.mqtt_cmd_topic_iterators_regex, mqtt_message.topic)
    if match:
        hub = Config.default_target_power_hub
        index1 = int(match.group(1))
        index2 = int(match.group(2))
        cmd = match.group(3)

        if cmd == 'power':
            handle_mqtt_power_message(bus, hub, index1, index2, mqtt_message.payload)
        else:
            logging.error("Unknown MQTT Command '%s'" % cmd)

def handle_mqtt_power_message(bus, hub, index1, index2, payload):
    logging.debug("Power Dose %s on Leiste %s for hub %s" % (index2, index1, hub))

    data = 0x02
    if payload == 'ON':
        data = 0x01
    elif payload == 'OFF':
        data = 0x00

    if not data == 0x02:
        arbitration_id = 0x01F00000
        arbitration_id = arbitration_id + (hub << 12) + 0x30 + index1

        payload = 0x0000
        for i in range(6-index2):
            payload = payload + (0x02 << i * 8)
        payload = payload + (data << (6 - index2) * 8)
        for i in range(index2-1):
            payload = payload + (0x02 << (5 - i) * 8)

        send_can_message(bus, arbitration_id, long_to_bytes(payload))

def long_to_bytes(val):
    result = []

    for i in range(8):
        result.insert(0, (val & (0xFF << i*8)) >> i*8)

    return bytearray(result)

def send_can_message(bus, id, data):
    logging.debug("Sending CAN message with arbitration id %s and data %s" %
                  (format(id, '#04x'), hexlify(data)))

    bus.send(can.Message(extended_id=True, arbitration_id=id, data=data))

def on_can_message(mqtt_client, can_message):
    logging.debug("received CAN message")
    arbitration_id = can_message.arbitration_id
    data = can_message.data

    logging.debug("arbitration_id: %s" % format(arbitration_id, '#10x'))

    message_type = (arbitration_id & 0xFF000000) >> 24

    if message_type == 0x04:
        logging.debug("Message Type: announcement")
        handle_local_event_message(mqtt_client, arbitration_id, data)
    else:
        logging.error("Unknown Message Type '%s'" % format(message_type, '#04x'))


def handle_local_event_message(mqtt_client, arbitration_id, data):
    node_type = (arbitration_id & 0x00F00000) >> 20

    if node_type == 0x0: # Bridge
        logging.debug("Node Type: Bridge")
    elif node_type == 0x1:  # Basis
        logging.debug("Node Type: Basis")
    elif node_type == 0xF:  # Power-Hub
        logging.debug("Node Type: Power-Hub")
        handle_power_hub_message(mqtt_client, arbitration_id, data)
    else:
        logging.error("Unknown Node Type '%s'" % format(node_type, '#03x'))


def handle_power_hub_message(mqtt_client, arbitration_id, data):
    node_id  = (arbitration_id & 0x000FF000) >> 12
    event_id = (arbitration_id & 0x00000FFF) >> 0

    logging.debug("Event ID: %s" % format(event_id, '#04x'))

    if event_id == 0x01:
        logging.debug('Sensor: start up - message ignored')
        return

    if event_id == 0x02:
        logging.debug('Sensor: keep alive - message ignored')
        return

    if event_id == 0x20:
        logging.debug('Sensor: Fuse - message ignored.')
        return

    if event_id <= 0x30 or event_id > 0x34:
        logging.warn('Not mapped Sensor "%s"' % format(event_id, '#04x'))
        return

    steckdosen_id = node_id * (event_id - 0x30)

    data = struct.unpack(">q", data)[0]

    logging.debug("CAN Payload: %s" % format(data, '#02x'))

    min_amp = (data & 0xFF00000000000000) >> 56
    max_amp = (data & 0x00FF000000000000) >> 48

    logging.debug("min amp %s" % min_amp)
    logging.debug("max amp %s" % max_amp)

    dose = []
    dose.append(int((data & 0x0000FF0000000000) >> 40))
    dose.append(int((data & 0x000000FF00000000) >> 32))
    dose.append(int((data & 0x00000000FF000000) >> 24))
    dose.append(int((data & 0x0000000000FF0000) >> 16))
    dose.append(int((data & 0x000000000000FF00) >>  8))
    dose.append(int((data & 0x00000000000000FF) >>  0))

    for i in range(6):
        topic = create_mqtt_stat_topic(steckdosen_id, i + 1)
        payload = payload_from_power_msg(dose[i])
        if payload:
            send_mqtt_message(mqtt_client, topic, payload)


def payload_from_power_msg(data):
    if data == 0x00:
        return 'OFF'
    elif data == 0x01:
        return 'ON'
    elif data == 0x02:
        return None
    else:
        logging.error('Invalid payload %s' % data)
        return None

def create_mqtt_stat_topic(steckdosen_id, dosen_id):
    return Config.mqtt_topic_template % (steckdosen_id, dosen_id, "stat/power")


def send_mqtt_message(mqtt_client, topic, payload):
    logging.debug("Sending MQTT Message '%s' to topic '%s'" % (payload, topic))

    try:
        result = mqtt_client.publish(topic, payload)
        if not (result[0] == mqtt.MQTT_ERR_SUCCESS):
            logging.error("Error publishing message \"%s\" to topic \"%s\". Return code %s: %s" % (
                payload, topic, str(result[0]), mqtt.error_string(result[0]
            )))
    except BaseException as e:
        logging.error(
            "Error relaying message {%s} '%s'. Error: {%s}" % (format(payload, '#2x'), topic, e))

def start():
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)

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
    mqtt_client.on_message = lambda client, userdata, mqtt_message: on_mqtt_message(bus, client, userdata, mqtt_message)

    try:
        mqtt_errno = mqtt_client.connect(Config.mqtt_broker, Config.mqtt_broker_port, 60)
        if mqtt_errno != 0:
            raise Exception(mqtt.error_string(mqtt_errno))

        mqtt_client.loop_start()
    except BaseException as e:
        logging.error("MQTT error: %s" % e)
        bus.shutdown()
        notifier.stop()

    try:
        for i in range(1, Config.mqtt_topic_iterator1_max+1):
            for j in range(1, Config.mqtt_topic_iterator2_max + 1):
                subscription_topic = Config.mqtt_topic_template % (i, j, "cmd/power")

                logging.info("Adding MQTT subscription to '%s'" % subscription_topic)
                mqtt_client.subscribe(subscription_topic)
    except BaseException as e:
        logging.error("Error adding subscribtion \"%s\": %s" %
                      (Config.mqtt_topic_template, e))

    logging.info("Starting web server")
    run_simple('localhost', Config.http_port, httpApp, use_reloader=True, extra_files=["static/main.css", "templates/index.html"])

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
    start()
