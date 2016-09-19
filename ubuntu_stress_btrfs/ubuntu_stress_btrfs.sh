#!/bin/bash

#
# Default mount options
#
OPTS="autodefrag clear_cache commit=5 commit=300 compress compress=lzo compress=zlib compress-force compress-force=lzo compress-force=zlib compress=no discard enospc_debug flushoncommit inode_cache noacl nobarrier nodatacow nodatasum nospace_cache notreelog recovery rescan_uuid_tree skip_balance space_cache ssd ssd_spread thread_pool=4 thread_pool=64 user_subvol_rm_allowed noatime"

#
#  Simple mix of options
#
OPTS="$OPTS autodefrag,compress,discard,noacl,nodatasum,recovery,space_cache,noatime,inode_cache"
#
#  Fast and loose options
#
OPTS="$OPTS nodatasum,nodatacow,noacl,nobarrier,notreelog,space_cache,thread_pool=128,ssd,ssd_spread"
#
#  Slow options
#
OPTS="$OPTS autodefrag,clear_cache,commit=1,compress-force=zlib,enospc_debug,flushoncommit,metadata_ratio=1,recovery,thread_pool=4"
#OPTS="autodefrag,clear_cache,commit=1,compress-force=lzo,enospc_debug,flushoncommit,metadata_ratio=1,recovery,thread_pool=4"
#
#  Mix of options
#
OPTS="$OPTS autodefrag,commit=900,compress-force=zlib,inode_cache,max_inline=65536,metadata_ratio=128,nobarrier,skip_balance,thread_pool=512"

N=$(getconf _NPROCESSORS_ONLN)
N=$((N * 2))
#STRESS_NG=/home/king/stress-ng/stress-ng
#DURATION=6s
INFO="--verify --times --metrics-brief --syslog --keep-name"
#IONICE="--ionice-class rt --ionice-level 0"
#SCHED="--sched idle"
SCHED=""
#MNT=/tmp/mnt-btrfs
#DEV=/dev/vdb1
#LOG="/tmp/btrfs-falure.log"
LOOPFILE=loop.tmp

if [ -z $DEV ]; then
	echo "Error: device not defined in DEV"
	exit 1
fi
if [ -z $MNT ]; then
	echo "Error: mount point not defined in MNT"
	exit 1
fi
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

echo "STARTING.."
set -o posix ; set
echo "DONE!"

do_tidy()
{
	echo "Interrupted. Cleaning up.."
	killall -9 stress-ng &> /dev/null
	cd
	umount $DEV &> /dev/null
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
	if [ $(grep "$DEV" /proc/mounts | wc -l) -gt 0 ]; then
		echo "Device $DEV is already mounted!"
		exit 1
	fi
	mk=0
	if [ ! -d $MNT ]; then
		mkdir $MNT
		if [ $? -ne 0 ]; then
			echo "Failed to create mount point $MNT, terminating!"
			exit 1
		fi
		mk=1
	fi

	dmesg -c > /dev/null
	mkfs.btrfs --force --mixed $DEV >& /dev/null
	if [ $? -ne 0 ]; then
		echo "Failed to format $DEV, terminating!"
		exit 1
	fi
	sync
	#
	# Ensure clean state
	#
	echo 1 > /proc/sys/vm/drop_caches
	sleep 1
	echo 2 > /proc/sys/vm/drop_caches
	sleep 1
	echo 3 > /proc/sys/vm/drop_caches
	sleep 1
	#
	# And away we go!
	#
	echo " "
	echo "--------------------------------------------------------------------------------"
	echo "Mount options: $OPT"
	echo "Stress test:   ${STRESS_NG} $*"
	echo "Device:        $DEV"
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
	mount $DEV $MNT -o $OPT,fatal_errors=panic
	if [ $? -ne 0 ]; then
		echo "Failed to mount, aborting test!"
		return
	fi

	do_check $OPT $* &
	pid=$!

	cd $MNT
	${STRESS_NG} $*
	rc=$?
	if [ $rc -ne 0 ]; then
		echo "Stress-ng returned error: $rc"
	fi
	cd - > /dev/null
	killall -9 stress-ng &> /dev/null
	sync
	sleep 1
	umount $DEV
	if [ $? -ne 0 ]; then
		echo "Failed to umount, terminating!"
		exit 1
	fi
	sleep 1
	kill -TERM $pid &> /dev/null

	if [ $mk -eq 1 ]; then
		rmdir $MNT
	fi
	echo "================================================================================"
}

trap "do_tidy" SIGINT SIGTERM SIGHUP

if [ $EUID -ne 0 ]; then
	echo "This needs to be run as root"
	exit 1
fi

if [ $(grep "$DEV" /proc/mounts | wc -l) -gt 0 ]; then
	echo "Cannot run test, $DEV is already mounted!"
	exit 1
fi

rm -f $LOG
touch $LOG

LOSETUP=0
if [ $DEV = "loop" ]; then
	LOSETUP=1
	DEV=$(losetup -f)
	truncate -s 256M $LOOPFILE
	losetup $DEV $LOOPFILE
fi

#
#  Run through all the different mount options..
#
for OPT in $OPTS
do
	#
	#  Single stressors..
	#
	#  cking: commented these out as they take far too long
	#  and we test this functionality with the "hammer it to death"
	#  stressors.  We leave these in just in case we need them
	#  at some point in the future.
	#
	#do_test $INFO $IONICE $SCHED -t $DURATION --dentry $N --dentries 100000
	#do_test $INFO $IONICE $SCHED -t $DURATION --dir $N
	#do_test $INFO $IONICE $SCHED -t $DURATION --fallocate $N  --fallocate-bytes 256M
	#do_test $INFO $IONICE $SCHED -t $DURATION --flock $N
	#do_test $INFO $IONICE $SCHED -t $DURATION --hdd $N --hdd-opts sync,wr-rnd,rd-rnd,fadv-willneed,fadv-rnd --hdd-bytes 256M --hdd-write-size 512
	#do_test $INFO $IONICE $SCHED -t $DURATION --hdd $N --hdd-opts wr-seq,rd-rnd --hdd-bytes 128M --hdd-write-size 128K
	#do_test $INFO $IONICE $SCHED -t $DURATION --lease $N
	#do_test $INFO $IONICE $SCHED -t $DURATION --link $N  --symlink $N
	#do_test $INFO $IONICE $SCHED -t $DURATION --lockf $N
	#do_test $INFO $IONICE $SCHED -t $DURATION --seek $N --seek-size 256M
	#do_test $INFO $IONICE $SCHED -t $DURATION --utime $N --utime-fsync
	#
	#  And hammer it to death..
	#
	do_test $INFO $IONICE $SCHED -t $DURATION --hdd $N --hdd-opts sync,wr-rnd,rd-rnd,fadv-willneed,fadv-rnd \
		--link $N --symlink $N --lockf $N --seek $N --aio $N --aio-requests 32 --dentry $N --dir $N \
		--dentry-order stride --fallocate $N --fstat $N --dentries 65536 --io 1 --lease $N --mmap 0 \
		--mmap-file --mmap-async --open $N --rename $N --hdd-bytes 128M --fallocate-bytes 128M \
		--mmap-bytes 128M --hdd-write-size 512 --ionice-class besteffort --ionice-level 0
done

if [ $LOSETUP -eq 1 ]; then
	losetup -d $DEV
	rm -f $LOOPFILE
fi

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
