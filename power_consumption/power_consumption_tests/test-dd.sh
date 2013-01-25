#!/bin/bash
#
#  Simple power measurement test, stress VM subsystem
#

. ${SCRIPT_PATH}/test-common.sh

#
# Block size and number to copy
#
DD_BS=1M
DD_COUNT=262144

dd_copy()
{
	sleep 5
	
	echo "DEBUG: dd starting" > /dev/stderr
	$SENDTAG localhost $METER_TAGPORT "TEST_BEGIN dd copy"
	# Just 1 run for this test
	$SENDTAG localhost $METER_TAGPORT "TEST_RUN_BEGIN dd copy"
	(dd if=/dev/zero bs=$DD_BS count=$DD_COUNT | cat | cat | dd of=/dev/zero) > /dev/null 2>&1
	$SENDTAG localhost $METER_TAGPORT "TEST_RUN_END dd copy"
	$SENDTAG localhost $METER_TAGPORT "TEST_END dd copy"
	$SENDTAG localhost $METER_TAGPORT "TEST_QUIT"
	echo "DEBUG: dd complete" > /dev/stderr
}

#
# Run for a maximum of 15 minutes, after which LOGMETER finishes w/o a full
# set of results.
#
SAMPLES=$((900 / $SAMPLE_INTERVAL))

echo "DEBUG: Invoking dd" > /dev/stderr

dd_copy &

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

echo "DEBUG: dd test completed." > /dev/stderr
echo "DEBUG: samples gathered in $SAMPLES_LOG :" > /dev/stderr
echo "DEBUG: -------------------------" > /dev/stderr
cat $SAMPLES_LOG > /dev/stderr
echo "DEBUG: -------------------------" > /dev/stderr

#
# Compute stats, scale by 100 because we are using a power clamp
#
$STATSTOOL -S -T -X 100 $SAMPLES_LOG | grep metric: | sed 's/metric:/metric:dd_copy_/'

echo "DEBUG: statstool output:" > /dev/stderr
echo "DEBUG: -------------------------" > /dev/stderr
$STATSTOOL -S -T -X 100 $SAMPLES_LOG | grep metric: | sed 's/metric:/metric:dd_copy_/' > /dev/stderr
echo "DEBUG: -------------------------" > /dev/stderr
echo "DEBUG: test-dd.sh now complete" > /dev/stderr
