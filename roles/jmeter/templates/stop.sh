#!/bin/bash

netstat -tulpn | awk '/1099/ && /LISTEN/ {split($7, a, "/"); system("kill -9 " a[1])}'