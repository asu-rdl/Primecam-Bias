#!/bin/bash
sudo systemctl stop sparkybiasd.service
cd /home/asu/
source /home/asu/.venv/bin/activate
python3 /home/asu/update_daemon.py