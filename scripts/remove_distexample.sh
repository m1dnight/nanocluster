#!/bin/bash

export ASDF_DATA_DIR=/home/pi/.asdf
export PATH="$ASDF_DATA_DIR/shims:$ASDF_DATA_DIR:$PATH"

cd /home/pi/teleconnect
just release
