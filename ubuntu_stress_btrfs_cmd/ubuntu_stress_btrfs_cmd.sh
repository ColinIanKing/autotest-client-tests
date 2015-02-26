#!/bin/bash
#
# Default mount options
#
OPTS="autodefrag clear_cache commit=5 commit=300 compress compress=lzo compress=zlib compress-force compress-force=lzo compress-force=zlib compress=no discard enospc_debug flushoncommit inode_cache noacl nobarrier nodatacow nodatasum notreelog recovery rescan_uuid_tree skip_balance space_cache ssd ssd_spread thread_pool=4 thread_pool=64 user_subvol_rm_allowed noatime"

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
#
#  Mix of options
#
OPTS="$OPTS autodefrag,commit=900,compress-force=zlib,inode_cache,max_inline=65536,metadata_ratio=128,nobarrier,skip_balance,thread_pool=512"

N=$(getconf _NPROCESSORS_ONLN)
N=$((N * 2))
SCHED=""
#MNT=/tmp/mnt-btrfs
#DEV=/dev/vdb1
#LOG="/tmp/btrfs-falure.log"

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
if [ -z $STRESS_NG ]; then
	echo "Error: stress-ng not defined in STRESS_NG"
	exit 1
fi

fill_fs()
{
	depth=$1
	depth=$(expr $depth - 1)
	if [ $depth -ge 0 ]; then
		for i in $(seq 100)
		do
			f=`mktemp XXXXXXXXXXXXXX`
			s=$(($RANDOM*10/32767))
			dd if=/dev/urandom of=$f bs=1K count=$s &> /dev/null

			f=`mktemp XXXXXXXXXXXXXX`
			s=$(($RANDOM*10/32767))
			dd if=/dev/zero of=$f bs=1K count=$s &> /dev/null
		done

		for i in $(seq 5)
		do
			local d=`mktemp -d XXXXXXXXXXXXXX.dir`
			local here=$(pwd)
			cd $d
				fill_fs $depth
			cd $here &> /dev/null
			for j in $(seq 8)
			do
				local e=`mktemp -d XXXXXX.dir`
				cp --reflink -rp $d $e
			done
			for j in $(seq 14)
			do
				local e=`mktemp -d XXXXXX.dir`
				cp -rp $d $e
			done
		done
	fi
}

fill_dir()
{
	depth=$1
	echo -n "Populating file system (depth $depth), "
	cd $2
	fill_fs $depth
	cd - &> /dev/null
	echo Size: $(du -hs $2), Files: $(find $2 | wc -l)
	#echo "Syncing and flushing.."
	sync
	#
	# Ensure clean state
	#
	echo 1 > /proc/sys/vm/drop_caches
	echo 2 > /proc/sys/vm/drop_caches
	echo 3 > /proc/sys/vm/drop_caches
}

do_unmount()
{
	n=0
	while true
	do
		umount $DEV >& /dev/null
		if [ $? -ne 0 ]; then
			n=$((n + 1))
			if [ $n -lt 15 ]; then
				echo "Failed to umount, retrying!"
				lsof $MNT
				do_kill
				sleep 1
			else
				echo "Failed to umount, abort!"
				exit
			fi
		else
			break
		fi
	done
}

do_kill()
{
	while [ "$(pidof stress-ng)" != "" ]
	do
		killall -SIGINT stress-ng >& /dev/null
		sleep 1
		killall -SIGINT stress-ng >& /dev/null
		sleep 1
		killall -9 stress-ng >& /dev/null
		sleep 2
	done
}

do_tidy()
{
	echo "Interrupted. Cleaning up.."
	do_kill
	cd
	do_unmount
	exit 1
}

btrfs_check_kernel()
{
	warn=$(dmesg | grep "WARNING:" | wc -l)
	call=$(dmesg | grep "Call Trace:" | wc -l)
	t=$((warn + $call))
	if [ $t -gt 0 ]; then
		echo "FAIL: Found kernel warning and/or call trace:"
		echo " "
		dmesg
		echo " " >> $LOG
		echo "FAIL: Found kernel warning and/or call trace:" >> $LOG
		echo " " >> $LOG
		echo "TEST: $*" >> $LOG
		echo >> $LOG
		dmesg -c >> $LOG
		echo " " >> $LOG
	fi
}

btrfs_quota()
{
	btrfs quota enable $MNT
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs qoata enable returned $ret"
		return 1
	fi
	btrfs quota rescan -s $MNT
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs qoata rescan returned $ret"
		return 1
	fi
	btrfs quota disable $MNT
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs qoata disable returned $ret"
		return 1
	fi
	return 0
}

btrfs_check()
{
	rc=0

	do_kill
	cd
	do_unmount

	btrfs check $DEV
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs check returned $ret"
		rc=1
	fi

	mount $DEV $MNT -o $OPT,fatal_errors=panic
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs check re-mount returned $ret"
		rc=1
	fi

	return $rc
}

btrfs_restore()
{
	rc=0
	TMP_DIR=/tmp/btrfs-restore-$$

	do_kill
	cd
	do_unmount

	mkdir $TMP_DIR
	if [ ! -d $TMP_DIR ]; then
		echo "FAIL: btrfs restore failed to create temporary directory"
	fi
	btrfs restore $DEV $TMP_DIR
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs restore returned $ret"
		rc=1
	fi


	mount $DEV $MNT -o $OPT,fatal_errors=panic
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs restore re-mount returned $ret"
		rc=1
	fi

	cd $TMP_DIR
	diffs=$(find . -exec diff {} $MNT/{} \; | grep -v Common | wc -l)
	if [ $diffs -gt 0 ]; then
		echo "FAIL: found $diffs file differences"
	fi
	cd
	rm -rf $TMP_DIR

	return $rc
}

btrfs_chunk_recover()
{
	rc=0

	do_kill
	cd
	do_unmount

	btrfs rescue chunk-recover -v -y $DEV
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs rescue chunk-recover returned $ret"
		rc=1
	fi

	mount $DEV $MNT -o $OPT,fatal_errors=panic
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs rescue chunk-recover re-mount returned $ret"
		rc=1
	fi

	return $rc
}

btrfs_super_recover()
{
	rc=0

	do_kill
	cd
	do_unmount

	btrfs rescue super-recover -v -y $DEV
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs rescue super-recover returned $ret"
		rc=1
	fi

	mount $DEV $MNT -o $OPT,fatal_errors=panic
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs rescue super-recover re-mount returned $ret"
		rc=1
	fi

	return $rc
}


btrfs_balance()
{
	btrfs balance start -v -d -m -s --force $MNT &
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs balance start returned $ret"
		btrfs balance cancel $MNT
		return 1
	fi
	sleep 0.5
	btrfs balance status -v $MNT
	btrfs balance pause $MNT
	ret=$?
	if [ $ret -eq 2 ]; then
		# balance already done..
		btrfs scrub status -d $MNT
		return 0
	fi
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs balance pause returned $ret"
		btrfs balance cancel $MNT
		return 1
	fi
	sleep 0.5
	btrfs balance status -v $MNT
	btrfs balance resume $MNT &
	ret=$?
	if [ $ret -eq 2 ]; then
		# balance lready done..
		btrfs scrub status -d $MNT
		return 0
	fi
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs balance resume returned $ret"
		btrfs balance cancel $MNT
		return 1
	fi
	sleep 0.5
	btrfs balance status -v $MNT
	btrfs balance cancel $MNT
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs balance pause returned $ret"
		btrfs balance cancel $MNT
		return 1
	fi
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs balance cancel returned $ret"
		return 1
	fi
	btrfs balance status -v $MNT
	return 0
}

btrfs_scrub()
{
	btrfs scrub start -d $MNT &
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs scrub start returned $ret"
		btrfs scrub cancel $MNT
		return 1
	fi
	btrfs scrub status -d $MNT
	btrfs scrub cancel $MNT
	ret=$?
	if [ $ret -eq 2 ]; then
		# scrub already done..
		btrfs scrub status -d $MNT
		return 0
	fi
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs scrub cancel returned $ret"
		btrfs scrub cancel $MNT
		return 1
	fi
	btrfs scrub status -d $MNT
	btrfs scrub resume -d $MNT &
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs scrub resume returned $ret"
		btrfs scrub cancel $MNT
		return 1
	fi
	btrfs scrub status -d $MNT
	btrfs scrub cancel $MNT
	if [ $ret -eq 2 ]; then
		# scrub already done..
		btrfs scrub status -d $MNT
		return 0
	fi
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAIL: btrfs scrub cancel returned $ret"
		return 1
	fi
	return 0
}

do_test()
{
	fill_depth=$1
	shift
	where=$(pwd)
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
	echo 2 > /proc/sys/vm/drop_caches
	echo 3 > /proc/sys/vm/drop_caches
	#
	# And away we go!
	#
	echo " "
	echo "--------------------------------------------------------------------------------"
	echo "Mount options: $OPT"
	echo "Stress test:   $*"
	echo " "
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
	fill_dir $fill_depth $MNT

	cd $MNT

	#
	#  Create some initial file system contention for a short while
	#
	${STRESS_NG} --hdd 0 --hdd-bytes 64M --seek 0 --link 0 --lockf 0 --flock 0 --dentry 0 --dir 0 --fallocate 0 --fallocate-bytes 32M --lease 0 --keep-name --syslog -t 20 &> /dev/null &
	pid=$!

	echo " "
	echo "Starting: $*"
	echo " "
	$*
	rc=$?

	do_kill
	cd $where
	echo "--------------------------------------------------------------------------------"
	echo " "
	if [ $rc -ne 0 ]; then
		echo "FAIL: Command $* returned error: $rc"
	else
		echo "PASS: Command $* succeeded"
	fi
	echo " "

	do_unmount
	btrfs_check_kernel

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



#
#  Run through all the different mount options..
#
for OPT in $OPTS
do
	#
	#  Simple stressors..
	#
	do_test 3 "btrfs filesystem df $MNT"
	#do_test 1 "btrfs filesystem show $MNT"
	do_test 1 "btrfs filesystem sync $MNT"
	do_test 3 "btrfs filesystem defragment -c -r -f $MNT"
	do_test 3 "btrfs filesystem resize -200m $MNT"
	do_test 1 "btrfs filesystem label $MNT TEST123"
	do_test 3 "btrfs_balance"
	do_test 2 "btrfs_restore"
	do_test 3 "btrfs_scrub"
	do_test 1 "btrfs check $DEV"
	do_test 1 "btrfs_quota"
	do_test 3 "btrfs device stats $MNT"
	do_test 3 "btrfs_check"
	do_test 3 "btrfs_chunk_recover"
	do_test 1 "btrfs_super_recover"
done

echo " "
echo "Completed"
echo " "
if [ -s $LOG ]; then
	echo "FAIL: Kernel issues: SOME"
	cat $LOG
else
	echo "PASS: Kernel issues: NONE"
fi
echo " "
