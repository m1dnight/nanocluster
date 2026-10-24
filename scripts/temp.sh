#!/bin/bash

temp=$(vcgencmd measure_temp)
hostname=$(hostname)

echo "${hostname} ${temp}"