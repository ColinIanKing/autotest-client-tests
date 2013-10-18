#
# Common code between power consumption tests,
# gather environment settings and flush dirty
# pages before we run the tests
#

#
# Number of samples
#
SAMPLES=${SAMPLES:-150}
#
# Interval between samples in seconds
#
SAMPLE_INTERVAL=${SAMPLE_ITERVAL:-2}
#
# Default for tests is to wait SETTLE_DURATION before kicking
# of a new test.
#
SETTLE_DURATION=${SETTLE_DURATION:-30}

#
# Duration of stress test, plus a bit of slop
#
DURATION=$(((SAMPLES + 1) * $SAMPLE_INTERVAL))

CPUS=$(cat /proc/cpuinfo  | grep processor | wc -l)

echo "DEBUG: SAMPLES: $SAMPLES" > /dev/stderr
echo "DEBUG: SAMPLE_INTERVAL: $SAMPLE_INTERVAL" > /dev/stderr
echo "DEBUG: SETTLE_DURATION: $SETTLE_DURATION" > /dev/stderr
echo "DEBUG: DURATION: $DURATION" > /dev/stderr
echo "DEBUG: CPUS: $CPUS" > /dev/stderr

#
# Meter configs need setting
#
if [ -z $METER_ADDR ]; then
	echo "DEBUG: METER_ADDR not configured!" > /dev/stderr
	exit 1
fi
if [ -z $METER_PORT ]; then
	echo "DEBUG: METER_PORT not configured!" > /dev/stderr
	exit 1
fi
if [ -z $METER_TAGPORT ]; then
	echo "DEBUG: METER_TAGPORT not configured!" > /dev/stderr
	exit 1
fi
if [ -z $SAMPLES_LOG ]; then
	echo "DEBUG: SAMPLES_LOG not configured!" > /dev/stderr
	exit 1
fi
if [ -z $STATISTICS_LOG ]; then
	echo "DEBUG: STATISTICS_LOG not configured!" > /dev/stderr
	exit 1
fi

echo "DEBUG: METER_ADDR: $METER_ADDR" > /dev/stderr
echo "DEBUG: METER_PORT: $METER_PORT" > /dev/stderr
echo "DEBUG: METER_TAGPORT: $METER_TAGPORT" > /dev/stderr
echo "DEBUG: SAMPLES_LOG: $SAMPLES_LOG" > /dev/stderr
echo "DEBUG: STATISTICS_LOG: $STATISTICS_LOG" > /dev/stderr

#
#  Tools for gathering data and analysis
#
if [ -z $LOGMETER ]; then
	echo "DEBUG: LOGMETER not configured!" > /dev/stderr
	exit 1
fi
if [ ! -x $LOGMETER ]; then
	echo "DEBUG: Cannot find LOGMETER at $LOGMETER" > /dev/stderr
	exit 1
fi

if [ -z $SENDTAG ]; then
	echo "DEBUG: SENDTAG not configured!" > /dev/stderr
	exit 1
fi
if [ ! -x $SENDTAG ]; then
	echo "DEBUG: Cannot find SENDTAG at $SENDTAG" > /dev/stderr
	exit 1
fi

if [ -z $STATSTOOL ]; then
	echo "DEBUG: STATSTOOL not configured!" > /dev/stderr
	exit 1
fi
if [ ! -x $STATSTOOL ]; then
	echo "DEBUG: Cannot find STATSTOOL at $STATSTOOL" > /dev/stderr
	exit 1
fi
if [ -z $STRESS ]; then
	echo "DEBUG: STRESS not configured!" > /dev/stderr
	exit 1
fi

echo "DEBUG: LOGMETER: $LOGMETER" > /dev/stderr
echo "DEBUG: SENDTAG: $SENDTAG" > /dev/stderr
echo "DEBUG: STATSTOOL: $STATSTOOL" > /dev/stderr
echo "DEBUG: STRESS: $STRESS" > /dev/stderr

echo "DEBUG: Flushing dirty pages and dropping caches" > /dev/stderr
#
# Flush dirty pages and drop caches
#
sync; sleep 1
sync; sleep 1
(echo 1 | sudo tee /proc/sys/vm/drop_caches) > /dev/null
(echo 2 | sudo tee /proc/sys/vm/drop_caches) > /dev/null
(echo 3 | sudo tee /proc/sys/vm/drop_caches) > /dev/null
sync; sleep 1

echo "DEBUG: Waiting for system to settle: $SETTLE_DURATION seconds" > /dev/stderr

#
# Wait a little to settle
#
sleep ${SETTLE_DURATION}

echo "DEBUG: Test setup completed" > /dev/stderr
