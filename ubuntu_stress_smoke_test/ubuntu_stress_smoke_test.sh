#!/bin/bash 

SYS_ZSWAP_ENABLED=/sys/module/zswap/parameters/enabled

#
# Stress test duration in seconds
#
DURATION=5
#
# Number of stress-ng instances per stressor
#
INSTANCES=4
#
# Generic stress-ng options
#
#STRESS_OPTIONS="--ignite-cpu --maximize --syslog --verbose --verify"
STRESS_OPTIONS="--ignite-cpu --syslog --verbose --verify --oomable"
#
# Tests that can lock up some kernels or are CPU / arch specific, so exclude them for now
#
EXCLUDE="rdrand numa quota apparmor cpu-online kcmp copy-file exec "
EXCLUDE+="spawn remap stack oom-pipe resources opcode sockfd vforkmany sockpair "
EXCLUDE+="bind-mount funccall ioport watchdog mlockmany idle-page clone "
#
# Tests that are not kernel specific
#
EXCLUDE+="atomic bsearch heapsort hsearch longjmp lsearch matrix memcpy nop qsort "
EXCLUDE+="rdrand str tsc vecmath wcs zlib matrix-3d "
#
# Tests that are known to cause breakage
#
EXCLUDE+="xattr efivar "
#
# Tests that should be skipped on KVM kernels
#
[ "$(uname -r | awk -F'-' '{print $NF}')" == "kvm" ] && EXCLUDE+="dnotify "
#
# Tests that break on specific kernel versions and we won't fix
#
ver=$(uname -r | cut -d'.' -f1-2)
if [ "$ver" == "4.20" ]; then
	#
	#  Broken on 4.20, fixed in 5.0-rc2
	#
	EXCLUDE+="dccp sctp "
fi

#
# Get built-in stressor names
#
STRESSORS=$(./stress-ng --stressors)
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

#
#  Try an ensure that this script and parent won't be oom'd
#
set_max_oom_level()
{
	if [ -e /proc/self/oom_score_adj ]; then
		echo -900 > /proc/self/oom_score_adj
		echo -900 > /proc/$PPID/oom_score_adj
	elif [ -e /proc/self/oom_adj ]; then
		echo -14 > /proc/self/oom_adj
		echo -14 > /proc/$PPID/oom_adj
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
# Enable Zswap if it is available and save original setting
# to restore later.
#
if [ -e ${SYS_ZSWAP_ENABLED} ]; then
	ORIGINAL_SYS_ZSWAP_SETTING=$(cat ${SYS_ZSWAP_ENABLED})
	echo Y > ${SYS_ZSWAP_ENABLED}
	SYS_ZSWAP_SETTING=$(cat ${SYS_ZSWAP_ENABLED})
else
	SYS_ZSWAP_SETTING="N"
fi

#
#  Always add 1GB of swap to ensure swapping is exercised
#
SWPIMG=$PWD/swap.img

dd if=/dev/zero of=${SWPIMG} bs=1M count=1024
chmod 0600 ${SWPIMG}
mkswap ${SWPIMG}
swapon -a ${SWPIMG}

echo " "
echo "Machine Configuration"
echo "Physical Pages:  $(getconf _PHYS_PAGES)"
echo "Pages available: $(getconf _AVPHYS_PAGES)"
echo "Page Size:       $(getconf PAGE_SIZE)"
echo "Zswap enabled:   ${SYS_ZSWAP_SETTING}"
echo " "
echo "Free memory:"
free
echo " "
echo "Number of CPUs: $(getconf _NPROCESSORS_CONF)"
echo "Number of CPUs Online: $(getconf _NPROCESSORS_ONLN)"
echo " "
set_max_oom_level

count=0
s1=$(secs_now)
for s in ${STRESSORS}
do
	if not_exclude $s "$EXCLUDE"
	then
		count=$((count + 1))
		dmesg -c >& /dev/null
		echo "$s STARTING"
		./stress-ng -v -t ${DURATION} --${s} ${INSTANCES} ${STRESS_OPTIONS} &> ${TMP_FILE}
		ret=$?
		echo "$s RETURNED $ret"

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
echo "  Oomed:   $(echo $oomed | wc -w), $oomed"
echo "  Passed:  $(echo $passed | wc -w), $passed"
echo "  Badret:  $(echo $badret | wc -w), $badret"
echo " "
echo "Tests took $dur seconds to run"

swapoff -a ${SWPIMG}
rm ${SWPIMG}

if [ -e ${SYS_ZSWAP_ENABLED} ]; then
	echo ${ORIGINAL_SYS_ZSWAP_SETTING} > ${SYS_ZSWAP_ENABLED}
fi

exit $rc
