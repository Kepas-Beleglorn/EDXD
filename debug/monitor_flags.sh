#!/usr/bin/bash
cd /mnt/data/pycharm_projects/EDXD
source .venv/bin/activate
export PYTHONPATH=$PWD
python3 debug/show_status_flags.py
deactivate
