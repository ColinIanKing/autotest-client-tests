#!/bin/bash

TESTDIR=vfat-test-$$

MNT=/mnt/$TESTDIR
VFAT_IMAGE_PATH=$1

#
#  Various vfat mount options
#
OPTS="allow_utime=20 utf8=1 uni_xlate=1 uid=0 gid=0 umask=777 dmask=777 fmask=777 nonumtail=1 check=s check=r shortname=lower shortname=win95 shortname=winnt showexec flush"

#
# Limit to max of 2 CPUs else we get way too much I/O
# contention making tests take forever to complete
#
N=2
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

	VFAT_IMAGE0=${VFAT_IMAGE_PATH}/block-dev-0
	truncate -s 2G ${VFAT_IMAGE0}

	mkfs.vfat ${VFAT_IMAGE0}
	mkdir -p ${MNT}
	mount ${VFAT_IMAGE0} ${MNT} -o ${OPT}

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
	echo "VFAT options:  $OPT"
	echo "Stress test:   ${STRESS_NG} $*"
	echo "VFAT_IMAGE path:     $VFAT_IMAGE_PATH"
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
	echo "umounting vfat"
	umount ${MNT}
	echo "destroying VFAT_IMAGEs"
	dd if=/dev/zero of=$VFAT_IMAGE0 bs=1M count=1024 >& /dev/null
	rm -rf $VFAT_IMAGE0
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

#
#  Run through all the different mount options..
#
for OPT in $OPTS
do
	#
	#  And hammer it to death..
	#
	do_test $INFO $IONICE $SCHED -t $DURATION --hdd $N --hdd-opts sync,wr-rnd,rd-rnd,fadv-willneed,fadv-rnd \
		--lockf $N --seek $N --aio $N --aio-requests 32 --dentry $N --dir $N \
		--dentry-order stride --fallocate $N --fstat $N --dentries 100 --lease $N --mmap 0 \
		--mmap-file --mmap-async --open $N --rename $N --hdd-bytes 4M --fallocate-bytes 4M \
		--chdir $N --rename $N \
		--mmap-bytes 4M --hdd-write-size 512
done

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
