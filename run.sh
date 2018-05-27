#!/bin/bash
./start_can0.sh

export PYTHONPATH='.'
python can2mqtt.py
