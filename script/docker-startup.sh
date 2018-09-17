#!/bin/bash
# Add socat for RFXTRX
config="/config/socatdevices.cfg"
# Stop on errors
set -e
if [ -e $config ]
then
set -f
oldifs="$IFS"

echo "Setup socat devices"
while read cmd; do
    IFS=';'; arrayIN=($cmd)
    device=${arrayIN[0]}
    port=${arrayIN[1]}
    echo "device = $device";
    echo "port = $port";
    /usr/src/app/socat.sh "$device" "$port" &
done < "$config"

IFS="$oldifs"
set +f
fi

sleep 5

echo "Starting homeassistant custom startup"
exec python -m homeassistant --config /config
