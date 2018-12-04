#!/bin/bash

VFAT_IMAGE_PATH=vfat-test-$$
VFAT_IMAGE=${VFAT_IMAGE_PATH}/vfat-image-$$.img
VFAT_IMAGE_SIZE=256M

MNT=/mnt/vfat-test-$$
TIMEOUT=120


#
#  Various vfat mount options
#
OPTS="allow_utime=20 utf8=1 uni_xlate=1 uid=0 gid=0 umask=777 dmask=777 fmask=777 nonumtail=1 check=s check=r shortname=lower shortname=win95 shortname=winnt showexec"

#
# Limit to max of 2 CPUs else we get way too much I/O
# contention making tests take forever to complete
#
MAX_STRESSORS=2
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

do_log()
{
	echo $*
	echo $* > /dev/kmsg
}

do_tidy()
{
	echo "Interrupted. Cleaning up.."
	killall -9 stress-ng &> /dev/null
	cd
	umount $MNT
	rm -f $VFAT_IMAGE
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

check_dead()
{
	local procs=$(ps -C stress-ng | grep -v PID | wc -l)
	if [ $procs -eq 0 ]; then
		do_log "stress-ng now terminated"
		return 0
	fi
	return 1
}

#
#  forcefully kill stress-ng and stress-ng children
#  aka "use the hammer"
#
do_terminate()
{
	local pid=$1
	local N=0

	while true
	do
		if check_dead; then break; fi
		kill -TERM $pid &> /dev/null
		sleep 1
		if check_dead; then break; fi
		kill -ALRM $pid &> /dev/null
		sleep 1
		if check_dead; then break; fi
		killall -TERM stress-ng &> /dev/null
		sleep 5
		if check_dead; then break; fi
		killall -ALRM stress-ng &> /dev/null
		sleep 1
		if check_dead; then break; fi
		killall -KILL stress-ng &> /dev/null
		sleep 1
		if check_dead; then break; fi
		N=$((N+1))
		if [ $N -gt 60 ]; then
			do_log Failed to terminate stress-ng, may have issues unmounting
			break
		fi
	done
}

do_test()
{
	if [ $(grep "$MNT" /proc/mounts | wc -l) -gt 0 ]; then
		do_log "$MNT is already mounted!"
		exit 1
	fi

	dmesg -c > /dev/null
	do_log "Testing: $*"

	mkdir -p ${VFAT_IMAGE_PATH}
	if [ $? -ne 0 ]; then
		do_log "mkdir -p ${VFAT_IMAGE_PATH} failed"
		exit 1
	fi

	truncate -s ${VFAT_IMAGE_SIZE} ${VFAT_IMAGE}
	if [ $? -ne 0 ]; then
		do_log "truncate -s ${VFAT_IMAGE_SIZE} ${VFAT_IMAGE} failed"
		rm -rf ${VFAT_IMAGE_PATH}
		exit 1
	fi

	LOOP_DEV=$(losetup --show -f ${VFAT_IMAGE})
	if [ $? -ne 0 ]; then
		do_log "losetup --show -f ${VFAT_IMAGE} failed"
		rm -rf ${VFAT_IMAGE_PATH}
		exit 1
	fi

	do_log "Created loop image ${VFAT_IMAGE} on ${LOOP_DEV}"

	sleep 1

	mkfs.vfat ${LOOP_DEV}
	mkdir -p ${MNT}
	mount ${VFAT_IMAGE} ${MNT} -o ${OPT}

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
	echo "VFAT options:  ${OPT}"
	echo "Stress test:   ${STRESS_NG} $*"
	echo "VFAT_IMAGE:    ${VFAT_IMAGE_PATH}"
	echo "Image Size:    ${VFAT_IMAGE_SIZE}"
	echo "Loop device:   ${LOOP_DEV}"
	echo "Mount point:   ${MNT}"
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
	chkpid=$!

	#
	#  run stress-ng in the background and monitor loop, killing it
	#  if necessary if it overruns
	#
	cd ${MNT}
	${STRESS_NG} $* 2>&1 | grep "info:" &
	sngpid=$!
	do_log "Started, PID $sngpid"
	terminated=0
	N=0
	while true
	do
		if check_dead; then
			chkrun=$(lsof $MNT | wc -l)
			if [ $chkrun -eq 0 ]; then
				terminated=1
				do_log "Stopped, PID $sngpid (after $N seconds)"
			else
				do_log "Still $chkrun processes on ${MNT}, retrying kill"
			fi
			break
		fi
		N=$((N+1))
		if [ $N -gt $TIMEOUT  ]; then
			do_log "Timed out waiting for stress-ng to finish"
			break
		fi
		sleep 1
	done
	#
	#  Timed out, Vulcan death grip required
	#
	if [ $terminated -eq 0 ]; then
		do_log "Forcefully killing, PID $sngpid (after $N seconds)"
		do_terminate $sngpid
	fi

	cd - > /dev/null

	sleep 1
	do_log "umounting vfat ${LOOP_DEV} ${MNT}"
	umount ${MNT}
	if [ $? -ne 0 ]; then
		do_log "umount vfat ${MNT} failed"
	fi
	sleep 1
	do_log "destroying loop ${LOOP_DEV}"
	losetup -d ${LOOP_DEV}
	if [ $? -ne 0 ]; then
		do_log "losetup -d ${LOOP_DEV} failed"
	fi
	sleep 1
	kill -TERM $chkpid &> /dev/null
	sleep 1
	rm -rf ${VFAT_IMAGE_PATH}
	rmdir ${MNT}

	echo "================================================================================"
}

trap "do_tidy" SIGINT SIGTERM SIGHUP

if [ $EUID -ne 0 ]; then
	echo "This needs to be run as root"
	exit 1
fi

if [ $(grep "$MNT" /proc/mounts | wc -l) -gt 0 ]; then
	do_log "$MNT is already mounted!"
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
	do_test $INFO $IONICE $SCHED -t $DURATION \
		--hdd $MAX_STRESSORS --hdd-opts sync,wr-rnd,rd-rnd,fadv-willneed,fadv-rnd \
		--lockf $MAX_STRESSORS --seek $MAX_STRESSORS --aio $MAX_STRESSORS \
		--aio-requests 32 --dentry $MAX_STRESSORS --dir $MAX_STRESSORS \
		--dentry-order stride --fallocate $MAX_STRESSORS \
		--fstat $MAX_STRESSORS --dentries 100 \
		--lease $MAX_STRESSORS --open $MAX_STRESSORS \
		--rename $MAX_STRESSORS --hdd-bytes 4M --fallocate-bytes 2M \
		--chdir $MAX_STRESSORS --rename $MAX_STRESSORS \
		--hdd-write-size 512
done

echo " "
echo "Completed"
echo " "
if [ -s $LOG ]; then
	do_log "Kernel issues: SOME"
	cat $LOG
else
	do_log "Kernel issues: NONE"
fi
echo " "
