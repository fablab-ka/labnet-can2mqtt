class Config:
    mqtt_broker = "192.168.1.6"
    mqtt_broker_port = "1883"
    mqtt_client_id = "bride_1"
    mqtt_topic_template = "/FLKA/Steckdosen/Hub%02d/Leiste%02d/Dose%02d/%s"
    mqtt_topic_iterator1_max = 2
    mqtt_topic_iterator2_max = 4
    mqtt_topic_iterator3_max = 6

    http_port = None

    mqtt_cmd_topic_iterators_regex = '^/FLKA/Steckdosen/Hub([0-9]*)/Leiste([0-9]*)/Dose([0-9]*)/cmd/(.*)$'

    canbus_interface = "can0"
    canbus_type = "socketcan"
    #canbus_type = "virtual"

    log_level = "error"
    #log_file = None
    log_file = "/var/log/can2mqtt.log"
