#!/usr/bin/env bash

if [ ! -d "./mullvad-wireguard-proxy" ]; then
    mkdir -p ./mullvad-wireguard-proxy/assets
    BASE_URL='https://raw.githubusercontent.com/mietzen/xbar-mullvad-wireguard-proxy-plugin/main'
    wget -qO ./mullvad-wireguard-proxy/mullvad-wireguard-proxy.py "$BASE_URL/mullvad-wireguard-proxy.py"
    wget -qO ./mullvad-wireguard-proxy/requierments "$BASE_URL/requierments"
    wget -qO ./mullvad-wireguard-proxy/assets/mullvad_icon.png "$BASE_URL/assets/mullvad_icon.png"
fi

cd mullvad-wireguard-proxy

if [ ! -d "./.venv" ]; then
    python3 -m venv .venv
    .venv/bin/pip3 install -r ./requierments -q
fi
./.venv/bin/python3 ./mullvad-wireguard-proxy.py
