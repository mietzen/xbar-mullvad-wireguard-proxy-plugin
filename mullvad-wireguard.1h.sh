#!/usr/bin/env bash

cd mullvad-wireguard

if [ ! -d "./venv" ]; then
    python3 -m venv .venv
    .venv/bin/pip3 install -r ./requierments
fi
.venv/bin/python3.11 ./mullvad-wireguard.1h.py
