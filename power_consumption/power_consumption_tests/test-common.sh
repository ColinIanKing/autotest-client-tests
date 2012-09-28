#
# Common code between power consumption tests,
# gather environment settings and flush dirty
# pages before we run the tests
#

#
# Number of samples
#
SAMPLES=${SAMPLES:-60}
#
# Interval between samples in seconds
#
SAMPLE_INTERVAL=${SAMPLE_ITERVAL:-5}
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

#
# Meter configs need setting
#
if [ -z $METER_ADDR ]; then
	echo "METER_ADDR not configured!" > /dev/stderr
	exit 1
fi
if [ -z $METER_PORT ]; then
	echo "METER_PORT not configured!" > /dev/stderr
	exit 1
fi
if [ -z $METER_TAGPORT ]; then
	echo "METER_TAGPORT not configured!" > /dev/stderr
	exit 1
fi
if [ -z $SAMPLES_LOG ]; then
	echo "SAMPLES_LOG not configured!" > /dev/stderr
	exit 1
fi
if [ -z $STATISTICS_LOG ]; then
	echo "STATISTICS_LOG not configured!" > /dev/stderr
	exit 1
fi

#
#  Tools for gathering data and analysis
#
if [ -z $LOGMETER ]; then
	echo "LOGMETER not configured!" > /dev/stderr
	exit 1
fi
if [ ! -x $LOGMETER ]; then
	echo "Cannot find LOGMETER at $LOGMETER" > /dev/stderr
	exit 1
fi

if [ -z $SENDTAG ]; then
	echo "SENDTAG not configured!" > /dev/stderr
	exit 1
fi
if [ ! -x $SENDTAG ]; then
	echo "Cannot find SENDTAG at $SENDTAG" > /dev/stderr
	exit 1
fi

if [ -z $STATSTOOL ]; then
	echo "STATSTOOL not configured!" > /dev/stderr
	exit 1
fi
if [ ! -x $STATSTOOL ]; then
	echo "Cannot find STATSTOOL at $STATSTOOL" > /dev/stderr
	exit 1
fi

#
# Flush dirty pages and drop caches
#
sync; sleep 1
sync; sleep 1
(echo 1 | sudo tee /proc/sys/vm/drop_caches) > /dev/null
(echo 2 | sudo tee /proc/sys/vm/drop_caches) > /dev/null
(echo 3 | sudo tee /proc/sys/vm/drop_caches) > /dev/null
sync; sleep 1

#
# Wait a little to settle
#
sleep ${SETTLE_DURATION}
