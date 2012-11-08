#!/bin/bash
#
#  Simple power measurement test, running the chromium browser for a while
#

. ${SCRIPT_PATH}/test-common.sh

DISPLAY=:0 chromium-browser --user-data-dir=/home/ubuntu --load-extension=${SCRIPT_PATH}/extension &
sleep $DURATION
sudo killall chromium-browser
