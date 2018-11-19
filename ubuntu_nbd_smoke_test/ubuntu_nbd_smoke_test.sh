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
NBD_DUMMY_CONFIG=/tmp/nbd_config_dummy.conf
NBD_PORT=9999

do_tidy()
{
	umount ${MNT}
	sleep 1
	nbd-client -d ${NBD_DEV}
	sleep 1
	killall -9 nbd-server &> /dev/null
	kill -TERM $pid &> /dev/null
	rm -f ${NBD_IMAGE_PATH}
}

do_check()
{
	trap "exit 0" SIGINT SIGTERM

	while true
	do
		warn=$(dmesg | grep "WARNING:" | wc -l)
		call=$(dmesg | grep "Call Trace:" | wc -l)
		ioerror=$(dmesg | grep "I/O error.nbd" | wc -l)
		t=$((warn + call + ioerror))
		if [ $t -gt 0 ]; then
			echo "Found kernel warning, IO error and/or call trace:"
			echo " "
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
	echo "TESTING: $*" > /dev/kmsg

	dd if=/dev/zero of=${NBD_IMAGE_PATH} bs=1M count=128 >& /dev/null
	echo done
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
	pid=$!

	#nbd-server -V

	nbd-server ${NBD_PORT} ${NBD_IMAGE_PATH} -C ${NBD_DUMMY_CONFIG} >& /dev/null
	if [ $? -ne 0 ]; then
		echo "nbd-server failed to start"
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
			echo "network block device ${NBD_DEV} was not created"
			do_tidy
			exit 1
		fi
		sleep 1
		N=$((N+1))
	done

	#
	# Wait for server to be available
	#
	N=0
	while true
	do
		if netstat -A inet6 -lnp | grep 9999.*nbd-server; then
			break;
		fi
		if [ $N -gt 20 ]; then
			echo "server is not listening"
			do_tidy
			exit 1
		fi
		sleep 1
		N=$((N+1))
	done
	sleep 5

	nbd-client -t 30 localhost ${NBD_PORT} ${NBD_DEV} >& /dev/null
	if [ $? -ne 0 ]; then
		echo "nbd-client failed to start"
		do_tidy
		exit 1
	fi

	mkfs.ext4 -F ${NBD_DEV} &> /dev/null
	sync
	sleep 5

	mkdir -p ${MNT}
	N=0
	while true
	do
		mount ${NBD_DEV} ${MNT}
		if [ $? -eq 0 ]; then
			break;
		fi
		if [ $N -gt 20 ]; then
			echo "mount on ${NBD_DEV} failed"
			do_tidy
			exit 1
		fi
		sleep 1
		N=$((N+1))
	done

	echo "Mount: "
	mount | grep ${NBD_DEV}
	n=$(mount | grep ${NBD_DEV} | wc -l)
	if [ $n -lt 0 ]; then
		echo "mount on ${NBD_DEV} failed"
		do_tidy
		exit 1
	fi
	echo ""

	echo "Free: "
	df ${MNT}
	echo ""

	(dd if=/dev/zero of=${MNT}/largefile bs=1M count=100) >& /dev/null
	if [ $? -ne 0 ]; then
		echo "failed to write 100MB to nbd mounted file system"
		do_tidy
		exit 1
	fi
	echo "Free: "
	df ${MNT}
	sync
	rm -f {MNT}/largefile
	if [ $? -ne 0 ]; then
		echo "failed to remove 100MB file from nbd mounted file system"
		do_tidy
		exit 1
	fi
	sync
	do_tidy

	echo "================================================================================"
}

trap "do_tidy" SIGINT SIGTERM SIGHUP

if [ $EUID -ne 0 ]; then
	echo "This needs to be run as root"
	exit 1
fi

modprobe nbd
if [ $? -ne 0 ]; then
	echo "Cannot load Network Block Device module nbd.o"
	exit 1
fi

rm -f $LOG
touch $LOG

do_test

modprobe -r nbd
if [ $? -ne 0 ]; then
	echo "Cannot unload Network Block Device module nbd.o"
	exit 1
fi

echo " "
echo "Completed"
echo " "
if [ -s $LOG ]; then
	echo "Kernel issues: "
	cat $LOG
	exit 1
else
	echo "Kernel issues: NONE"
fi
echo " "
