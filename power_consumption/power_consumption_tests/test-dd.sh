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
	
	$SENDTAG localhost $METER_TAGPORT "TEST_BEGIN dd copy"
	# Just 1 run for this test
	$SENDTAG localhost $METER_TAGPORT "TEST_RUN_BEGIN dd copy"
	(dd if=/dev/zero bs=$DD_BS count=$DD_COUNT | cat | cat | dd of=/dev/zero) > /dev/null 2>&1
	$SENDTAG localhost $METER_TAGPORT "TEST_RUN_END dd copy"
	$SENDTAG localhost $METER_TAGPORT "TEST_END dd copy"
	$SENDTAG localhost $METER_TAGPORT "TEST_QUIT"
}

#
# Run for a maximum of 15 minutes, after which LOGMETER finishes w/o a full
# set of results.
#
SAMPLES=$((900 / $SAMPLE_INTERVAL))

dd_copy &

#
# Gather samples
#
rm -f $SAMPLES_LOG
$LOGMETER --addr=$METER_ADDR --port=$METER_PORT --tagport=$METER_TAGPORT \
          --measure=c --acdc=AC \
	  --interval=$SAMPLE_INTERVAL --samples=$SAMPLES \
	  --out=$SAMPLES_LOG > /dev/null

#
# Compute stats, scale by 1000 because we are using a power clamp
#
$STATSTOOL -S -T -X 1000 $SAMPLES_LOG | grep metric: | sed 's/metric:/metric:dd_copy_/'
