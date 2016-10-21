#!/bin/bash 

#
# Stress test duration in seconds
#
DURATION=10
#
# Number of stress-ng instances per stressor
#
INSTANCES=4
#
# Generic stress-ng options
#
#STRESS_OPTIONS="--ignite-cpu --maximize --syslog --verbose --verify"
STRESS_OPTIONS="--ignite-cpu --syslog --verbose --verify"
#
# Tests that can lock up some kernels or are CPU / arch specific, so exclude them for now
#
EXCLUDE="rdrand numa quota apparmor cpu-online kcmp copy-file exec spawn remap stack oom-pipe resources"
#
# Get built-in stressor names
#
STRESSORS=$(./stress-ng --help | grep "\-ops " | awk '{print $1}' | sed 's/--//' | sed 's/-ops//g')
rc=0
TMP_FILE=/tmp/stress-$$.log

secs_now()
{
	date "+%s"
}

not_exclude()
{
	for x in $2
	do
		if [ $x == $1 ]
		then
			return 1
		fi
	done
	return 0
}

passed=""
failed=""
skipped=""
oopsed=""

count=0
s1=$(secs_now)
for s in ${STRESSORS}
do
	if not_exclude $s "$EXCLUDE"
	then
		count=$((count + 1))
		dmesg -c >& /dev/null
		./stress-ng -v -t ${DURATION} --${s} ${INSTANCES} ${STRESS_OPTIONS} &> ${TMP_FILE}
		ret=$?

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
		99)
			echo "$s FAILED (kernel oopsed)"
			oopsed="$oopsed $s"
			dmesg
			echo " "
			;;
		esac
		rm -f ${TMP_FILE}
	fi
done
s2=$(secs_now)
dur=$((s2 - $s1))

echo " "
echo "Summary:"
echo "  Stressors run: $count"
echo "  Skipped: $(echo $skipped | wc -w), $skipped"
echo "  Failed:  $(echo $failed | wc -w), $failed"
echo "  Oopsed:  $(echo $oopsed | wc -w), $oopsed"
echo "  Passed:  $(echo $passed | wc -w), $passed"
echo " "
echo "Tests took $dur seconds to run"

exit $rc
