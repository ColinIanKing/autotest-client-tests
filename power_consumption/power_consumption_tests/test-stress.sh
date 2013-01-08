#!/bin/bash
#
#  Simple power measurement test, stress CPUs, I/O and VM
#

. ${SCRIPT_PATH}/test-common.sh

#
# Kick off stress test
#
stress -t $DURATION --cpu $CPUS --io $CPUS --vm $CPUS > /dev/null 2>&1 &
pid=$!

#
# Gather samples
#
rm -f $SAMPLES_LOG
$LOGMETER --addr=$METER_ADDR --port=$METER_PORT --tagport=$METER_TAGPORT \
          --measure=c --acdc=AC \
	  --interval=$SAMPLE_INTERVAL --samples=$SAMPLES \
	  --out=$SAMPLES_LOG > /dev/null

#
# Wait for stress to complete
#
wait $pid

#
# Compute stats, scale by 100 because we are using a power clamp
#
$STATSTOOL -S -T -X 100 -a $SAMPLES_LOG | grep metric: | sed 's/metric:/metric:stress_all_/'
