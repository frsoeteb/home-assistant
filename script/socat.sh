#!/bin/bash
# Add socat for RFXTRX
device="$1"
port="$2"

if [ $# -ne 2 ]
  then
    echo "Illegal number of arguments"
    exit 1;
fi
if [ -z "$1" ]
  then
    echo "No argument 1 supplied"
    exit 1;
fi
if [ -z "$2" ]
  then
    echo "No argument 2 supplied"
    exit 1;
fi

# Stop on errors
while sleep 5;do /usr/bin/socat -ly PTY,link=$device,raw TCP4:$port;done
