#!/bin/bash
#
#  Simple power measurement test, stress IO SYNCs
#

. ${SCRIPT_PATH}/test-common.sh

IO_OPS=3308000

stress_iosync()
{
	sleep 5
	
	echo "DEBUG: stress iosync starting with $IO_OPS bogo ops" > /dev/stderr
	$SENDTAG localhost $METER_TAGPORT "TEST_BEGIN stress iosync"
	# Just 1 run for this test
	$SENDTAG localhost $METER_TAGPORT "TEST_RUN_BEGIN stress iosync"
	$STRESS --io $CPUS --io-ops $IO_OPS > /dev/null 2>&1
	$SENDTAG localhost $METER_TAGPORT "TEST_RUN_END stress iosync"
	$SENDTAG localhost $METER_TAGPORT "TEST_END stress iosync"
	$SENDTAG localhost $METER_TAGPORT "TEST_QUIT"
	echo "DEBUG: stress iosync complete" > /dev/stderr
}

#
# Run for a maximum of 15 minutes, after which LOGMETER finishes w/o a full
# set of results.
#
SAMPLES=$((900 / $SAMPLE_INTERVAL))

echo "DEBUG: Invoking stress iosync" > /dev/stderr

stress_iosync &

#
# Gather samples
#
echo "DEBUG: Starting logmeter $LOGMETER" > /dev/stderr
rm -f $SAMPLES_LOG
$LOGMETER --addr=$METER_ADDR --port=$METER_PORT --tagport=$METER_TAGPORT \
          --measure=c --acdc=AC \
	  --interval=$SAMPLE_INTERVAL --samples=$SAMPLES \
	  --out=$SAMPLES_LOG > /dev/null

echo "DEBUG: Logging completed" > /dev/stderr

echo "DEBUG: stress iosync completed." > /dev/stderr
echo "DEBUG: samples gathered in $SAMPLES_LOG :" > /dev/stderr
echo "DEBUG: -------------------------" > /dev/stderr
cat $SAMPLES_LOG > /dev/stderr
echo "DEBUG: -------------------------" > /dev/stderr

#
# Compute stats, scale by 100 because we are using a power clamp
#
$STATSTOOL -S -T -X 100 $SAMPLES_LOG | grep metric: | sed 's/metric:/metric:stress_IO_Sync_/'

echo "DEBUG: statstool output:" > /dev/stderr
echo "DEBUG: -------------------------" > /dev/stderr
$STATSTOOL -S -T -X 100 $SAMPLES_LOG | grep metric: | sed 's/metric:/metric:stress_IO_Sync_/' > /dev/stderr
echo "DEBUG: -------------------------" > /dev/stderr
echo "DEBUG: test-iosync.sh now complete" > /dev/stderr
