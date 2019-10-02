#!/bin/bash
#
# Copyright (C) 2018 Canonical
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
TESTDIR=nbd-test-$$

MNT=/mnt/$TESTDIR
LOG=/tmp/nbd-test-$$.log
NBD_IMAGE_PATH=/tmp/nbd_image.img
NBD_DEV=/dev/nbd0
NBD_CONFIG=/tmp/nbd-$$.conf
NBD_PORT=10809
NBD_BLOCK_SIZE=512
NBD_TIMEOUT=240

do_log()
{
        echo $*
        echo $* > /dev/kmsg
}

do_tidy()
{
	do_log "unmounting ${MNT}"
	umount ${MNT}
	sleep 1
	do_log "stopping client"
	nbd-client -d ${NBD_DEV}
	sleep 1
	do_log "killing server"
	killall -9 nbd-server &> /dev/null
	kill -TERM ${do_check_pid} &> /dev/null
	rm -f ${NBD_IMAGE_PATH}
}

do_tidy_files()
{
	rm -f ${LOG}
	rm -rf ${MNT}
}

do_check()
{
	trap "exit 0" SIGINT SIGTERM

	while true
	do
		warn=$(dmesg | grep "WARNING:" | wc -l)
		call=$(dmesg | grep "Call Trace:" | wc -l)
		ioerror=$(dmesg | grep "I/O error.*nbd" | wc -l)
		t=$((warn + call + ioerror))
		if [ $t -gt 0 ]; then
			do_log "Found kernel warning, IO error and/or call trace"
			do_log echo " "
			dmesg
			echo " " >> $LOG
			echo "Found kernel warning, IO error and/or call trace:" >> $LOG
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
	dmesg -c > /dev/null

	do_log "creating backing nbd image ${NBD_IMAGE_PATH}"
	dd if=/dev/zero of=${NBD_IMAGE_PATH} bs=1M count=128 >& /dev/null
	if [ $? -ne 0 ]; then
		do_log "dd onto ${NBD_IMAGE_PATH} failed"
		do_tidy
	fi
	sync

	#
	# And away we go!
	#
	echo " "
	echo "--------------------------------------------------------------------------------"
	echo "Image path:    $NBD_IMAGE_PATH"
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
	echo "Free space:"
	df -h
	echo "--------------------------------------------------------------------------------"
	echo " "

	do_check $* &
	do_check_pid=$!

	echo "[generic]" > ${NBD_CONFIG}
	echo "    allowlist = true" >> ${NBD_CONFIG}
	echo "" >> ${NBD_CONFIG}
	echo "[test]" >> ${NBD_CONFIG}
	echo "    port = ${NBD_PORT}" >> ${NBD_CONFIG}
	echo "    exportname = ${NBD_IMAGE_PATH}" >> ${NBD_CONFIG}

	nbd-server -C ${NBD_CONFIG}
	if [ $? -ne 0 ]; then
		do_log "nbd-server failed to start"
		do_tidy
		exit 1
	fi

	#
	#  Wait for udev to settle
	#
	N=0
	while true
	do
		if [ -b ${NBD_DEV} ]; then
			break;
		fi
		if [ $N -gt 20 ]; then
			do_log "network block device ${NBD_DEV} was not created"
			do_tidy
			exit 1
		fi
		sleep 1
		N=$((N+1))
	done

	do_log NBD device ${NBD_DEV} created

	#
	# Wait for server to be available
	#
	N=0
	while true
	do
		n=$(sudo nbd-client -l localhost | grep test | wc -l)
		if [ $n -gt 0 ]; then
			do_log "found nbd export"
			break;
		fi
		if [ $N -gt 20 ]; then
			do_log "server is not listening"
			do_tidy
			exit 1
		fi
		sleep 1
		N=$((N+1))
	done
	sleep 1

	echo "NBD exports found:"
	nbd-client -l localhost | grep -v Negotiation

	do_log "starting client with NBD device ${NBD_DEV}"
	nbd-client -t ${NBD_TIMEOUT} -b ${NBD_BLOCK_SIZE} -p -N test localhost ${NBD_DEV}
	if [ $? -ne 0 ]; then
		do_log  "nbd-client failed to start"
		do_tidy
		exit 1
	fi

	do_log "creating ext4 on ${NBD_DEV}"
	N=0
	while true
	do
		#
		#  This may fail if the device has not fully initiated on
		#  slow systems, so we need to have some retries.
		#
		mkfs.ext4 -v -D -F ${NBD_DEV} &> /dev/null
		if [ $? -eq 0 ]; then
			do_log "mkfs on ${NBD_DEV} succeeded after $N attempt(s)"
			break;
		fi
		if [ $N -gt 20 ]; then
			do_log "mkfs on ${NBD_DEV} failed"
			do_tidy
			exit 1;
		fi
		sleep 1
		N=$((N+1))
	done
	sync

	do_log "checking ext4 on ${NBD_DEV}"
	fsck -y ${NBD_DEV}
	if [ $? -ne 0 ]; then
		do_log "fsck on ${NBD_DEV} failed"
		do_tidy
		exit 1;
	fi

	mkdir -p ${MNT}
	if [ $? -ne 0 ]; then
		do_log "mkdir -p ${MNT} failed"
		do_tidy
	fi

	N=0
	while true
	do
		mount ${NBD_DEV} ${MNT}
		if [ $? -eq 0 ]; then
			break;
		fi
		if [ $N -gt 20 ]; then
			do_log "mount on ${NBD_DEV} failed"
			do_tidy
			exit 1
		fi
		sleep 1
		N=$((N+1))
	done

	echo ""
	echo "mount: "
	mount | grep ${NBD_DEV}
	n=$(mount | grep ${NBD_DEV} | wc -l)
	if [ $n -lt 0 ]; then
		do_log "mount on ${NBD_DEV} failed"
		do_tidy
		exit 1
	fi
	do_log "mounted on ${NBD_DEV}"
	echo ""

	echo "free: "
	df ${MNT}
	echo ""

	do_log "creating large file ${MNT}/largefile"

	(dd if=/dev/zero of=${MNT}/largefile bs=1M count=100) >& /dev/null
	if [ $? -ne 0 ]; then
		do_log "failed to write 100MB to nbd mounted file system"
		do_tidy
		exit 1
	fi

	ls -alh ${MNT}/largefile
	echo ""

	echo "free: "
	df ${MNT}
	echo ""
	sync

	do_log "removing file ${MNT}/largefile"
	rm -f {MNT}/largefile
	if [ $? -ne 0 ]; then
		do_log "failed to remove 100MB file from nbd mounted file system"
		do_tidy
		exit 1
	fi
	sync
	do_tidy

	rm -f ${NBD_CONFIG}

	echo "================================================================================"
}

trap "do_tidy" SIGINT SIGTERM SIGHUP

if [ $EUID -ne 0 ]; then
	echo "This needs to be run as root"
	exit 1
fi

modprobe nbd
if [ $? -ne 0 ]; then
	do_log "Cannot load Network Block Device module nbd.o"
	exit 1
fi

rm -f $LOG
touch $LOG

do_test

modprobe -r nbd
if [ $? -ne 0 ]; then
	do_log "Cannot unload Network Block Device module nbd.o"
	exit 1
fi

echo " "
echo "Completed"
echo " "
if [ -s $LOG ]; then
	echo "Kernel issues: "
	cat $LOG
	do_tidy_files
	exit 1
else
	echo "Kernel issues: NONE"
	do_tidy_files
fi
echo " "
