class Config:
    mqtt_broker = "192.168.1.6"
    mqtt_broker_port = "1883"
    mqtt_client_id = "bride_1"
    mqtt_topic_template = "/FLKA/Steckdosen/Leiste%s/Dose%s/"

    canbus_interface = "can0"
    canbus_type = "socketcan"

