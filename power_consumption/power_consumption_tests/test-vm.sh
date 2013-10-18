#!/bin/bash
#
#  Simple power measurement test, stress VM subsystem
#

. ${SCRIPT_PATH}/test-common.sh

VM_OPS=4405

stress_vm()
{
	sleep 5
	
	echo "DEBUG: stress vm starting with $VM_OPS bogo ops" > /dev/stderr
	$SENDTAG localhost $METER_TAGPORT "TEST_BEGIN stress vm"
	# Just 1 run for this test
	$SENDTAG localhost $METER_TAGPORT "TEST_RUN_BEGIN stress vm"
	$STRESS --vm $CPUS --vm-ops $VM_OPS > /dev/null 2>&1
	$SENDTAG localhost $METER_TAGPORT "TEST_RUN_END stress vm"
	$SENDTAG localhost $METER_TAGPORT "TEST_END stress vm"
	$SENDTAG localhost $METER_TAGPORT "TEST_QUIT"
	echo "DEBUG: stress vm complete" > /dev/stderr
}

#
# Run for a maximum of 15 minutes, after which LOGMETER finishes w/o a full
# set of results.
#
SAMPLES=$((900 / $SAMPLE_INTERVAL))

echo "DEBUG: Invoking stress vm" > /dev/stderr

stress_vm &

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

echo "DEBUG: stress vm completed." > /dev/stderr
echo "DEBUG: samples gathered in $SAMPLES_LOG :" > /dev/stderr
echo "DEBUG: -------------------------" > /dev/stderr
cat $SAMPLES_LOG > /dev/stderr
echo "DEBUG: -------------------------" > /dev/stderr

#
# Compute stats, scale by 100 because we are using a power clamp
#
$STATSTOOL -S -T -X 100 $SAMPLES_LOG | grep metric: | sed 's/metric:/metric:stress_VM_/'

echo "DEBUG: statstool output:" > /dev/stderr
echo "DEBUG: -------------------------" > /dev/stderr
$STATSTOOL -S -T -X 100 $SAMPLES_LOG | grep metric: | sed 's/metric:/metric:stress_VM_/' > /dev/stderr
echo "DEBUG: -------------------------" > /dev/stderr
echo "DEBUG: test-vm.sh now complete" > /dev/stderr
