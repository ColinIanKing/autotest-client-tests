#!/bin/bash
#
#  Simple power measurement test, stress CPUs, I/O and VM
#

. ${SCRIPT_PATH}/test-common.sh

#
# Kick off stress test
#
echo "DEBUG: Invoking stress tool for $DURATION seconds on $CPUS CPUs" > /dev/stderr
stress -t $DURATION --cpu $CPUS --io $CPUS --vm $CPUS > /dev/null 2>&1 &
pid=$!

#
# Gather samples
#
echo "DEBUG: Starting logmeter $LOGMETER" > /dev/stderr
rm -f $SAMPLES_LOG
$LOGMETER --addr=$METER_ADDR --port=$METER_PORT --tagport=$METER_TAGPORT \
          --measure=c --acdc=AC \
	  --interval=$SAMPLE_INTERVAL --samples=$SAMPLES \
	  --out=$SAMPLES_LOG > /dev/null

#
# Wait for stress to complete
#
echo "DEBUG: Logging completed, waiting for stress PID:$pid to complete" > /dev/stderr
wait $pid
echo "DEBUG: stress test completed." > /dev/stderr
echo "DEBUG: samples gathered in $SAMPLES_LOG :" > /dev/stderr
echo "DEBUG: -------------------------" > /dev/stderr
cat $SAMPLES_LOG > /dev/stderr
echo "DEBUG: -------------------------" > /dev/stderr

#
# Compute stats, scale by 100 because we are using a power clamp
#
$STATSTOOL -S -T -X 100 -a $SAMPLES_LOG | grep metric: | sed 's/metric:/metric:stress_all_/'

echo "DEBUG: statstool output:" > /dev/stderr
echo "DEBUG: -------------------------" > /dev/stderr
$STATSTOOL -S -T -X 100 -a $SAMPLES_LOG | grep metric: | sed 's/metric:/metric:stress_all_/' > /dev/stderr
echo "DEBUG: -------------------------" > /dev/stderr
echo "DEBUG: test-stress.sh now complete" > /dev/stderr
