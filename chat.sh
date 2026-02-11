#!/bin/bash

PROJECT_PATH="$HOME/Desktop/chatminal"
source "$PROJECT_PATH/venv/bin/activate"
python3 "$PROJECT_PATH/main.py" "$@"