#!/bin/bash
#
#  Simple power measurement test, idle system
#

. ${SCRIPT_PATH}/test-common.sh

#
# Gather samples
#
rm -f $SAMPLES_LOG
$LOGMETER --addr=$METER_ADDR --port=$METER_PORT --tagport=$METER_TAGPORT \
          --measure=c --acdc=AC \
	  --interval=$SAMPLE_INTERVAL --samples=$SAMPLES \
	  --out=$SAMPLES_LOG > /dev/null

#
# Compute stats, scale by 100 because we are using a power clamp
#
$STATSTOOL -S -T -X 100 -a $SAMPLES_LOG | grep metric: | sed 's/metric:/metric:idle_system_/'
