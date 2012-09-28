#!/bin/bash
#
#  Simple power measurement test, idle system
#

#
# Duration of test in seconds
#
DURATION=${DURATION:-60}

info=$(${EVENTSTAT} ${DURATION} 1 | grep "Total events")
#
# Use awk to get fields (we add 0 to turn a string into float)
# 
total_events=$(echo $info | awk '{printf "%f\n", $4 + 0.0}')
kernel_events=$(echo $info | awk '{printf "%f\n", $7 + 0.0}')
userspace_events=$(echo $info | awk '{printf "%f\n", $9 + 0.0}')
#
# Emit data
#
echo -e "total_events\t$total_events"
echo -e "kernel_events\t$kernel_events"
echo -e "userspace_events\t$userspace_events"
