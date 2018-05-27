class Config:
    mqtt_broker = "192.168.1.6"
    mqtt_broker_port = "1883"
    mqtt_client_id = "bride_1"
    mqtt_topic_template = "/FLKA/Steckdosen/Leiste%02d/Dose%02d/%s"
    mqtt_topic_iterator1_max = 4
    mqtt_topic_iterator2_max = 6
    default_target_power_hub = 1

    mqtt_cmd_topic_iterators_regex = '^/FLKA/Steckdosen/Leiste([0-9]*)/Dose([0-9]*)/cmd/(.*)$'

    canbus_interface = "can0"
    canbus_type = "socketcan"

    log_level = "error"
