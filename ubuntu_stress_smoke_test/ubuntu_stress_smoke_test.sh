#!/bin/bash 

# Maximum machine age in years
MAX_AGE=5
# minimum required memory in MB
MIN_MEM=$((3 * 1024))
# minimum free disk required in GB
MIN_DISK=$((4))
# maximum bogo ops per stressor
MAX_BOGO_OPS=3000

SYS_ZSWAP_ENABLED=/sys/module/zswap/parameters/enabled

MEMORY=$((1024 * 1024 * 1024))
MEMFREE_KB=$(grep "MemFree" /proc/meminfo  | awk '{ print $2}')
MEMFREE=$((MEMFREE_KB * 1024))
MEMFREE_90PC=$((MEMFREE * 90 / 100))
MEMFREE_LESS_512MB=$((MEMFREE - (512 * 1024 * 1024)))
if [ $MEMFREE_90PC -gt $MEMFREE_LESS_512MB ]; then
	MEMORY=$MEMFREE_LESS_512MB
else
	MEMORY=$MEMFREE_90PC
fi
if [ $MEMORY -lt $((512 * 1024 * 1024)) ]; then
	MEMORY=$((512 * 1024 * 1024))
fi
echo "Free memory: $((MEMFREE / (1024 * 1024))) MB"
echo "Memory used: $((MEMORY / (1024 * 1024))) MB"

CGROUP_MEM1=/sys/fs/cgroup/memory/stress-ng-test
CGROUP_LIMIT1=${CGROUP_MEM1}/memory.limit_in_bytes
CGROUP_MEM2=/sys/fs/cgroup/stress-ng-test
CGROUP_LIMIT2=${CGROUP_MEM2}/memory.max
CGROUP=$(grep "/sys/fs/cgroup" /proc/mounts | cut -d' ' -f1)
if [ $CGROUP == "cgroup2" ]; then
	echo "Using cgroup version 2"
	CGROUP_MEM=${CGROUP_MEM2}
	CGROUP_LIMIT=${CGROUP_LIMIT2}
else
	echo "Using cgroup version 2"
	CGROUP_MEM=${CGROUP_MEM1}
	CGROUP_LIMIT=${CGROUP_LIMIT1}
fi
if [ ! -d ${CGROUP_MEM} ]; then
	mkdir ${CGROUP_MEM}
fi
echo $MEMORY > ${CGROUP_LIMIT}

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
EXCLUDE+="rdrand str tsc vecmath wcs zlib matrix-3d l1cache "
#
# Tests that are known to cause breakage
#
EXCLUDE+="xattr efivar sysinfo sysinval "
#
# Currenly a new stress test can causes problems with s390x on older kernels
# https://bugs.launchpad.net/ubuntu/+source/linux/+bug/1905438
#
EXCLUDE+="uprobe "
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

check_message()
{
	echo "NOTE: $1, skipping test"
}

check_machine()
{
	hostname=$(hostname)
	processor=$(uname -p)
	skip=0
	case "$processor" in
	i386 | i486 | i586 | i686 | x86_64)
		datecheck=1

		manufacturer=$(dmidecode -s system-manufacturer)
		if [ "$manufacturer" == "QEMU" ]; then
			echo "QEMU instance, no firmware date checking"
			datecheck=0
		fi

		vendor=$(dmidecode -t 0x0000 | grep Vendor: | awk '{ print $2}')
		if [ -z "$vendor" ]; then
			vendor=$(dmidecode -t 0x000e | grep Vendor: | awk '{ print $2}')
		fi

		case "$vendor" in
		unknown | Unknown)
			check_message "Unknown BIOS vendor, ignoring machine"
			skip=1
			datecheck=0
			;;
		SeaBIOS)
			echo "SeaBIOS BIOS, using a VM, no date checking"
			datecheck=0
			;;
		*)
			;;
		esac

		if [ $datecheck -eq 1 ]; then
			year=$(date +%Y)
			year=$((year - $MAX_AGE))
			date=$(dmidecode -t 0x0000 | grep "Release Date:" | cut -d'/' -f3)
			if [ -z "$date" ]; then
				date=$(dmidecode -t 0x000e | grep "Release Date:" | cut -d'/' -f3)
			fi
			if [ ! -z "$date" ]; then
				if [ $date -lt $year  ]; then
					check_message "BIOS indicates machine is more then $MAX_AGE years old"
					skip=1
				fi
			fi
		fi
		;;
	*)
		echo "other"
		;;
	esac

	mem=$(free | grep Mem: | awk '{print $2}')
	mem=$((mem / 1024))
	if [ $mem -lt $MIN_MEM ]; then
		check_message "Machine has only $mem MB memory, requires at least $MIN_MEM MB"
		skip=1
	fi
	disk=$(df . -B 1024  | awk '{print $4}' | tail -1)
	disk=$((disk / 1048576))
	if [ $disk -lt $MIN_DISK ]; then
		check_message "Machine has only $disk GB free disk space, requires at least $MIN_DISK GB"
		skip=1
	fi

	if [ $skip -ne 0 ]; then
		exit 0
	fi

	echo "$hostname: $processor $mem MB memory, $disk GB disk"
}

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
		echo 0 > /proc/sys/vm/oom_kill_allocating_task
	fi
}

check_machine

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

#
#  Create 1GB swap file
#
swapoff ${SWPIMG} >& /dev/null
fallocate -l 1G ${SWPIMG}
if [ $? -ne 0 ]; then
	echo "FAILED: Count not create 1GB swap file, file system:"
	df
	exit 1
fi
chmod 0600 ${SWPIMG}
mkswap ${SWPIMG}
swapon ${SWPIMG}

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
echo
echo "Maximum bogo ops: ${MAX_BOGO_OPS}"
echo " "
set_max_oom_level
sleep 15
sync

#
#  Handle cases where cgroup settings are enabled or not
#
RUN_STRESS='./stress-ng'
if [ -e ${CGROUP_LIMIT} ]; then
	cgexec -g memory:stress-ng-test /bin/true
	#
	#  If cgexec works on trivial case then use it for stress-ng
	#
	if [ $? -eq 0 ]; then
		RUN_STRESS='cgexec -g memory:stress-ng-test ./stress-ng'
	else
		echo "WARNING: cgexec fails, is ${CGROUP} working correctly?"
	fi
fi

count=0
s1=$(secs_now)
for s in ${STRESSORS}
do
	if not_exclude $s "$EXCLUDE"
	then
		count=$((count + 1))
		dmesg -c >& /dev/null
		echo "$s STARTING"
		${RUN_STRESS} -v -t ${DURATION} --${s} ${INSTANCES} --${s}-ops ${MAX_BOGO_OPS} ${STRESS_OPTIONS} >& ${TMP_FILE}
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
			dmesg
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
		137)
			echo "$s OOMED (out of memory kills detected)"
			oomed="$oomed $s"
			;;
		*)
			echo "$s BADRET (unknown return status $ret)"
			badret="$badret $s"
			dmesg
			echo " "
			;;
		esac
		rm -f ${TMP_FILE}
	fi
done
s2=$(secs_now)
dur=$((s2 - $s1))

#kill -9 $pid >& /dev/null
#wait $pid

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

rmdir ${CGROUP_MEM} >& /dev/null

exit $rc
