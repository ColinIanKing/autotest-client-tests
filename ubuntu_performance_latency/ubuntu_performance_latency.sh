#!/bin/bash

STRESSOR=$1

#
# Stress test duration in seconds
#
DURATION=120
#
# Number of stress-ng instances per stressor
#
INSTANCES=1
#
# Generic stress-ng options
#
STRESS_OPTIONS="--syslog --verbose --oomable --metrics-brief "

#
# Get built-in stressor names
#
TMP_FILE=/tmp/stress-$$.log

secs_now()
{
	date "+%s"
}

#
#  Try an ensure that this script won't be oom'd
#
set_max_oom_level()
{
	if [ -e /proc/self/oom_score_adj ]; then
		echo -500 > /proc/self/oom_score_adj
	elif [ -e /proc/self/oom_adj ]; then
		echo -10 > /proc/self/oom_adj
	fi
	#
	# Ensure oom killer kills the stressor hogs rather
	# than the wrong random process (e.g. autotest!)
	#
	if [ -e /proc/sys/vm/oom_kill_allocating_task ]; then
		echo 1 > /proc/sys/vm/oom_kill_allocating_task
	fi
}

passed=""
failed=""
skipped=""
oopsed=""
oomed=""
badret=""

echo " "
echo "Machine Configuration"
echo "Physical Pages:  $(getconf _PHYS_PAGES)"
echo "Pages available: $(getconf _AVPHYS_PAGES)"
echo "Page Size:       $(getconf PAGE_SIZE)"
echo " "
echo "Free memory:"
free
echo " "
echo "Number of CPUs: $(getconf _NPROCESSORS_CONF)"
echo "Number of CPUs Online: $(getconf _NPROCESSORS_ONLN)"
echo " "
set_max_oom_level

BOGOS=""
s1=$(secs_now)
dmesg -c >& /dev/null
echo "$s STARTING $1"
./stress-ng -v -t ${DURATION} --cyclic 1 --${STRESSOR} ${INSTANCES} ${STRESS_OPTIONS} &> ${TMP_FILE}
ret=$?
echo "$s RETURNED $ret"

MEAN=$(grep mean: ${TMP_FILE}  | awk '{print $6}')
MODE=$(grep mode: ${TMP_FILE}  | awk '{print $9}')
MIN=$(grep min: ${TMP_FILE}  | awk '{print $6}')
MAX=$(grep min: ${TMP_FILE}  | awk '{print $9}')
s2=$(secs_now)
dur=$((s2 - $s1))
rm ${TMP_FILE}

echo " "
echo "Summary:"
echo "  mean: ${MEAN}"
echo "  mode: ${MODE}"
echo "  min:  ${MIN}"
echo "  max:  ${MAX}"
echo " "
echo "Tests took $dur seconds to run"
exit 0
