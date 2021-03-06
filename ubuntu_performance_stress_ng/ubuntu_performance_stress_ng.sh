#!/bin/bash

STRESSOR=$1
THRESHOLD=$2
RUNS=$3

#
# Stress test duration in seconds
#
DURATION=60
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
rc=0
TMP_FILE=/tmp/stress-$$.log
YML_FILE=/tmp/stress-$$.yml

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

#
#  Always add 1GB of swap to ensure swapping is exercised
#
SWPIMG=$PWD/swap.img

dd if=/dev/zero of=${SWPIMG} bs=1M count=1024 >& /dev/null
chmod 0600 ${SWPIMG}
mkswap ${SWPIMG}
swapon -a ${SWPIMG}

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
for i in $(seq ${RUNS})
do
	dmesg -c >& /dev/null
	echo "$s STARTING $1"
	rm -f ${YML_FILE}
	echo "./stress-ng -v -t ${DURATION} --${STRESSOR} ${INSTANCES} ${STRESS_OPTIONS} --yaml ${YML_FILE}"
	./stress-ng -v -t ${DURATION} --${STRESSOR} ${INSTANCES} ${STRESS_OPTIONS} --yaml ${YML_FILE} &> ${TMP_FILE}
	ret=$?
	echo "$s RETURNED $ret"

	cat ${YML_FILE}
	BOGO=$(grep bogo-ops-per-second-usr-sys-time ${YML_FILE}  | awk '{print $2}')
	echo "BOGO=${BOGO}"
	BOGOS="${BOGOS} ${BOGO}"
	rm -f ${YML_FILE}

	n=$(dmesg | grep "Out of memory:" | wc -l)
	if [ $ret -ne 0 -a $n -gt 0 ]; then
		ret=88
	fi

	n=$(dmesg | grep "Oops" | wc -l)
	if [ $n -gt 0 ]; then
		ret=99
	fi

	case $ret in
	0)
		echo "$s PASSED"
		passed="$passed $s"
		;;
	1)
		echo "$s SKIPPED (test framework out of resources or test should not be run)"
		skipped="$skipped $s"
		;;
	2)
		echo "$s FAILED"
		failed="$failed $s"
		cat ${TMP_FILE}
		echo " "
		rc=1
		;;
	3)
		echo "$s SKIPPED (stressor out of resources)"
		skipped="$skipped $s"
		;;
	4)
		echo "$s SKIPPED (stressor not implemented on this arch)"
		skipped="$skipped $s"
		;;
	5)
		echo "$s SKIPPED (premature signal killed stressor)"
		skipped="$skipped $s"
		;;
	6)
		echo "$s SKIPPED (premature child exit, this is a bug in the stress test)"
		skipped="$skipped $s"
		;;
	7)
		echo "$s PASSED (child bogo-ops metrics were not accurate)"
		passed="$passed $s"
		;;
	88)
		echo "$s OOMED (out of memory kills detected)"
		oomed="$oomed $s"
		;;
	99)
		echo "$s FAILED (kernel oopsed)"
		oopsed="$oopsed $s"
		dmesg
		echo " "
		rc=1
		;;
	*)
		echo "$s BADRET (unknown return status $ret)"
		badret="$badret $s"
		;;
	esac
	rm -f ${TMP_FILE}
done
s2=$(secs_now)
dur=$((s2 - $s1))

echo " "
echo "Summary:"
echo "  Stressors run: $count"
echo "  Skipped: $(echo $skipped | wc -w), $skipped"
echo "  Failed:  $(echo $failed | wc -w), $failed"
echo "  Oopsed:  $(echo $oopsed | wc -w), $oopsed"
echo "  Oomed:   $(echo $oomed | wc -w), $oomed"
echo "  Passed:  $(echo $passed | wc -w), $passed"
echo "  Badret:  $(echo $badret | wc -w), $badret"
echo "  BogoOps:${BOGOS}"
echo " "
echo "Tests took $dur seconds to run"

swapoff -a ${SWPIMG}
rm ${SWPIMG}

exit $rc
