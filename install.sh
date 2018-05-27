#!/bin/bash

pip install -r requirements.txt

echo "[Unit]
Description=Can to MQTT Bridge
After=network.target
[Service]
Type=simple
User=root
WorkingDirectory="$PWD"
ExecStart= "$PWD"/run.sh
[Install]
WantedBy=multi-user.target
" > /etc/systemd/system/can2mqtt.service

systemctl daemon-reload
systemctl enable can2mqtt.service
systemctl start can2mqtt.service

echo "installation finished"
