#!/usr/bin/env bash
# Logs APU package power (PPT, CPU+GPU together; no GPU-only sensor on Strix Halo) once a second.
# Usage: powerlog.sh <out.csv>   (runs until killed). Columns: unix_time, watts
P=$(ls /sys/class/drm/card*/device/hwmon/hwmon*/power1_average | head -1)
echo "unix_time,watts" > "$1"
while :; do printf '%s,%s\n' "$(date +%s.%N | cut -c1-14)" "$(awk '{printf "%.2f", $1/1e6}' "$P")" >> "$1"; sleep 1; done
