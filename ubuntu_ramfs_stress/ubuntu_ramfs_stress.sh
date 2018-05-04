#!/bin/bash

TESTDIR=ramfs-test-$$

MNT=/mnt/$TESTDIR

#
# Limit to max of 4 CPUs else we get way too much I/O
# contention making tests take forever to complete
#
N=4
INFO="--verify --times --metrics-brief --syslog --keep-name"
SCHED=""

if [ -z $LOG ]; then
	echo "Error: log file not defined in LOG"
	exit 1
fi
if [ -z $DURATION ]; then
	echo "Error: run duration not defined in DURATION"
	exit 1
fi
if [ -z $STRESS_NG ]; then
	echo "Error: stress-ng not defined in STRESS_NG"
	exit 1
fi

#echo "STARTING.."
#set -o posix ; set
#echo "DONE!"

do_tidy()
{
	echo "Interrupted. Cleaning up.."
	killall -9 stress-ng &> /dev/null
	cd
	umount $MNT
	rm -f $VFAT_IMAGE0
	exit 1
}

do_check()
{
	trap "exit 0" SIGINT SIGTERM

	while true
	do
		warn=$(dmesg | grep "WARNING:" | wc -l)
		call=$(dmesg | grep "Call Trace:" | wc -l)
		t=$((warn + $call))
		if [ $t -gt 0 ]; then
			echo "Found kernel warning and/or call trace:"
			echo " "
			dmesg
			echo " " >> $LOG
			echo "Found kernel warning and/or call trace:" >> $LOG
			echo " " >> $LOG
			echo "TEST: $*" >> $LOG
			echo >> $LOG
			dmesg -c >> $LOG
			echo " " >> $LOG
		fi
		sleep 1
	done
}

do_test()
{
	if [ $(grep "$MNT" /proc/mounts | wc -l) -gt 0 ]; then
		echo "$MNT is already mounted!"
		exit 1
	fi

	dmesg -c > /dev/null
	echo "TESTING: $*" > /dev/kmsg

	mkdir -p ${MNT}
	mount -t ramfs none ${MNT} -o maxsize=128000

	#
	# Ensure clean state
	#
	echo 1 > /proc/sys/vm/drop_caches
	echo 2 > /proc/sys/vm/drop_caches
	echo 3 > /proc/sys/vm/drop_caches
	#
	# And away we go!
	#
	echo " "
	echo "--------------------------------------------------------------------------------"
	echo "Stress test:   ${STRESS_NG} $*"
	echo "Mount point:   $MNT"
	echo "Date:         " $(date)
	echo "Host:         " $(hostname)
	echo "Kernel:       " $(uname -rv)
	echo "Machine:      " $(uname -npi)
	echo "CPUs online:  " $(getconf _NPROCESSORS_ONLN)
	echo "CPUs total:   " $(getconf _NPROCESSORS_CONF)
	echo "Page size:    " $(getconf PAGE_SIZE)
	echo "Pages avail:  " $(getconf _AVPHYS_PAGES)
	echo "Pages total:  " $(getconf _PHYS_PAGES)
	echo "--------------------------------------------------------------------------------"
	echo " "
	echo "VFAT options:  $OPT" > /dev/kmsg
	echo "Stress test:   ${STRESS_NG} $*" > /dev/kmsg
	echo "Mount point:   $MNT" > /dev/kmsg
	echo " "

	do_check $OPT $* &
	pid=$!

	cd $MNT
	${STRESS_NG} $*
	rc=$?
	case $rc in
	0)	echo "Stress-ng exited with no errors"
		;;
	1)	echo "Stress-ng framework error, stressor not run"
		;;
	2)	echo "Stress-ng stressor failed, error: $rc"
		;;
	3)	echo "Stress-ng stressor ran out of memory or disk space"
		;;
	*)	echo "Stress-ng unknown error: $rc"
		;;
	esac

	cd - > /dev/null
	killall -9 stress-ng &> /dev/null
	sync
	sleep 1
	echo "umounting ramfs"
	umount ${MNT}
	dd if=/dev/zero of=$VFAT_IMAGE0 bs=1M count=1024 >& /dev/null
	kill -TERM $pid &> /dev/null

	echo "================================================================================"
}

trap "do_tidy" SIGINT SIGTERM SIGHUP

if [ $EUID -ne 0 ]; then
	echo "This needs to be run as root"
	exit 1
fi

if [ $(grep "$MNT" /proc/mounts | wc -l) -gt 0 ]; then
	echo "$MNT is already mounted!"
	exit 1
fi

rm -f $LOG
touch $LOG

do_test $INFO $IONICE $SCHED -t $DURATION --hdd $N --hdd-opts sync,wr-rnd,rd-rnd,fadv-willneed,fadv-rnd \
	--link $N --symlink $N --lockf $N --seek $N --aio $N --aio-requests 32 --dentry $N --dir $N \
	--dentry-order stride --fallocate $N --fstat $N --dentries 65536 --io 1 --lease $N --mmap 0 \
	--mmap-file --mmap-async --open $N --rename $N --hdd-bytes 32M --fallocate-bytes 32M \
	--chdir $N --chmod $N --filename $N --rename $N \
	--mmap-bytes 32M --hdd-write-size 512

echo " "
echo "Completed"
echo " "
if [ -s $LOG ]; then
	echo "Kernel issues: SOME"
	cat $LOG
else
	echo "Kernel issues: NONE"
fi
echo " "
