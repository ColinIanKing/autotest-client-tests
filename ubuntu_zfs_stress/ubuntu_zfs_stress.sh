#!/bin/bash

POOL=testpool
TESTDIR=test

MNT=/$POOL/$TESTDIR
MYPWD=$(pwd)

#
# ZFS options
#

#
# Compression settings
#
OPTS="$OPTS compression=on compression=off compression=lzjb compression=gzip compression=gzip-1 compression=gzip-9 compression=zle compression=lz4"

#
# atime settings
#
OPTS="$OPTS atime=on atime=off"

#
# acltype settings
#
OPTS="$OPTS acltype=noacl acltype=posixacl"

#
# checksum settings
#
OPTS="$OPTS checksum=on checksum=off checksum=fletcher2 checksum=fletcher4 checksum=sha256"

#
# copies settings
#
OPTS="$OPTS copies=1 copies=2 copies=3"

#
# dedup settings
#
OPTS="$OPTS dedup=on dedup=off dedup=verify dedup=sha256"

#
# logbias settings
#
OPTS="$OPTS logbias=latency logbias=throughput"

#
# primarycache settings
#
OPTS="$OPTS primarycache=all primarycache=none primarycache=metadata"

#
# recordsize settings
#
OPTS="$OPTS recordsize=512 recordsize=4096 recordsize=65536"

#
# redundant metadata settings
#
OPTS="$OPTS redundant_metadata=all redundant_metadata=most"

#
# relatime settings
#
OPTS="$OPTS relatime=on relatime=off"

#
# sync settings
#
OPTS="$OPTS sync=standard sync=always sync=disabled"

#
# vscan settings
#
OPTS="$OPTS vscan=on vscan=off"

#
# xattr settings
#
OPTS="$OPTS xattr=on xattr=off xattr=dir xattr=sa"

#
# ACL settings
#
OPTS="$OPTS aclinherit=discard aclinherit=noallow aclinherit=restricted aclinherit=passthrough"

#
# Mixed settings
#
OPTS="$OPTS compression=on,atime=on,acltype=posixacl,checksum=sha256,copies=3,dedup=sha256,logbias=latency,primarycache=all,recordsize=512,redundant_metadata=all,relatime=off,sync=always,vscan=on,xattr=on,aclinherit=passthrough"

#
# Mixed settinfs #2
#
OPTS="$OPTS compression=off,atime=off,acltype=noacl,checksum=off,copies=1,dedup=off,logbias=throughput,primarycache=none,recordsize=4096,redundant_metadata=most,relatime=on,sync=disabled,vscan=off,xattr=off,aclinherit=discard"

#
# Limit to max of 16 CPUs else we get way too much I/O
# contention making tests take forever to complete
#
N=$(getconf _NPROCESSORS_ONLN)
N=$((N * 2))
if [ $N -gt 16 ]; then
	N=16
fi
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
	zfs destroy $POOL/$TESTDIR
	zpool destroy $POOL
	rm -f $VDEV0 $VDEV1 $VDEV2 $VDEV3 $VDEV4
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

	truncate -s 1G ${MYPWD}/block-dev-0
	truncate -s 1G ${MYPWD}/block-dev-1
	truncate -s 1G ${MYPWD}/block-dev-2
	truncate -s 1G ${MYPWD}/block-dev-3
	truncate -s 1G ${MYPWD}/block-dev-4

	VDEV0=${MYPWD}/block-dev-0
	VDEV1=${MYPWD}/block-dev-1
	VDEV2=${MYPWD}/block-dev-2
	VDEV3=${MYPWD}/block-dev-3
	VDEV4=${MYPWD}/block-dev-4

	zpool create $POOL mirror $VDEV0 $VDEV1 -f
	zpool add $POOL mirror $VDEV2 $VDEV3 -f
	zpool add $POOL log $VDEV4 -f

	zfs create $POOL/$TESTDIR
	if [ $? -ne 0 ]; then
		echo "Failed to create $POOL/$TESTDIR, terminating!"
		zpool destroy $POOL
		rm -f $VDEV0 $VDEV1 $VDEV2 $VDEV3 $VDEV4
		exit 1
	fi
	sync
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
	echo "ZFS options:   $OPT"
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
	echo "ZFS options:   $OPT" > /dev/kmsg
	echo "Stress test:   ${STRESS_NG} $*" > /dev/kmsg
	echo "Mount point:   $MNT" > /dev/kmsg
	for o in $OPT
	do
		so=$(echo $o | sed 's/,/ /g')
		for s in $so
		do
			echo "zfs set $s $POOL/$TESTDIR"
			zfs set $s $POOL/$TESTDIR
			if [ $? -ne 0 ]; then
				echo "ZFS option $s in $o failed, aborting test!"
				echo " "
				zfs destroy $POOL/$TESTDIR
				zpool destroy $POOL
				return
			fi
		done
	done
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
	echo "destroying zfs"
	zfs destroy $POOL/$TESTDIR
	echo "destroying zpool"
	zpool destroy $POOL
	if [ $? -ne 0 ]; then
		echo "Failed to destory ZFS pool, terminating!"
		exit 1
	fi
	echo "destroying VDEVs"
	rm -f $VDEV0 $VDEV1 $VDEV2 $VDEV3 $VDEV4 $VDEV5
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
	#  Single stressors..
	#
	do_test $INFO $IONICE $SCHED -t $DURATION --chdir $N
	do_test $INFO $IONICE $SCHED -t $DURATION --chmod $N
	do_test $INFO $IONICE $SCHED -t $DURATION --dentry $N --dentries 100000
	do_test $INFO $IONICE $SCHED -t $DURATION --dir $N
	do_test $INFO $IONICE $SCHED -t $DURATION --fallocate $N  --fallocate-bytes 64M
	do_test $INFO $IONICE $SCHED -t $DURATION --filename $N
	do_test $INFO $IONICE $SCHED -t $DURATION --flock $N
	do_test $INFO $IONICE $SCHED -t $DURATION --fstat $N
	do_test $INFO $IONICE $SCHED -t $DURATION --hdd $N --hdd-opts sync,wr-rnd,rd-rnd,fadv-willneed,fadv-rnd --hdd-bytes 64M --hdd-write-size 512
	do_test $INFO $IONICE $SCHED -t $DURATION --hdd $N --hdd-opts wr-seq,rd-rnd --hdd-bytes 32M --hdd-write-size 32K
	do_test $INFO $IONICE $SCHED -t $DURATION --lease $N
	do_test $INFO $IONICE $SCHED -t $DURATION --link $N --symlink $N
	do_test $INFO $IONICE $SCHED -t $DURATION --lockf $N
	do_test $INFO $IONICE $SCHED -t $DURATION --rename $N
	do_test $INFO $IONICE $SCHED -t $DURATION --seek $N --seek-size 64M
	do_test $INFO $IONICE $SCHED -t $DURATION --utime $N --utime-fsync
	#
	#  And hammer it to death..
	#
	do_test $INFO $IONICE $SCHED -t $DURATION --hdd $N --hdd-opts sync,wr-rnd,rd-rnd,fadv-willneed,fadv-rnd \
		--link $N --symlink $N --lockf $N --seek $N --aio $N --aio-requests 32 --dentry $N --dir $N \
		--dentry-order stride --fallocate $N --fstat $N --dentries 65536 --io 1 --lease $N --mmap 0 \
		--mmap-file --mmap-async --open $N --rename $N --hdd-bytes 128M --fallocate-bytes 128M \
		--chdir $N --chmod $N --filename $N --rename $N \
		--mmap-bytes 128M --hdd-write-size 512 --ionice-class besteffort --ionice-level 0
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
