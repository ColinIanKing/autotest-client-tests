#!/bin/bash
#
# Copyright (C) 2017 Canonical
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

#
#  Trival "smoke test" blktrace tests just to see
#  if basic functionality works
#
TMPFILE=/tmp/blktrace-kernel-trace-$$.tmp

#
#  Time to wait for blktrace to gather final samples (seconds)
#
DURATION=10

#
#  Number of arbitary events to wait for, don't make this too
#  large
#
EVENTS=1024

#
#  Count of blocks to dd, should be much larger then $EVENTS
#
COUNT=$((EVENTS * 64))

passed=0
failed=0

#
#  Loopback image and mount point, image is 33% larger than
#  file to be dd'd.
#
START_DIR=$(pwd)
IMG_COUNT=$((COUNT * 133 / 100))
IMG=${START_DIR}/loop.img
MNT=${START_DIR}/mnt

inc_failed()
{
	failed=$((failed + 1))
	rc=1
}

inc_passed()
{
	passed=$((passed + 1))
}

get_dev()
{
	mount=$(stat -c '%m' $1 | tail -1)
	DEV=$(df $mount | grep dev | head -1 | cut -d' ' -f1)
	case $DEV in
		/dev/loop*)
		;;
		/dev/disk/by-*)
		;;
		/dev/*[0-9])
			DEV=$(echo $DEV | sed 's/[0-9]//g')
		;;
		*)
			echo "SKIPPED cannot determine block device $1 is located on (skipping test)"
			exit 0
		;;
	esac

	echo ""
	if [ -b "$DEV" ]; then
		echo "Using block device $DEV for path $1"
	else
		echo "SKIPPED cannot determine block device $1 is located on (skipping test) (tried $DEV)"
		exit 0
	fi
}

mount_debugfs()
{
	if [ ! -d /sys/kernel/debug ]; then
		mount -t debugfs nodev /sys/kernel/debug
		if [ $? -ne 0 ]; then
			echo "FAILED: cannot mount /sys/kernel/debug"
			exit 1
		fi
		unmount=1
	else
		unmount=0
	fi
}

umount_debugfs()
{
	if [ $unmount -eq 1 ]; then
		umount /sys/kernel/debug
	fi
}

mount_loopback()
{
	mkdir -p ${MNT}
	dd if=/dev/zero of=${START_DIR}/loop.img bs=1K count=${IMG_COUNT} >& /dev/null
	mkfs.ext4 ${IMG} >& /dev/null
	if [ $? -ne 0 ]; then
		echo "FAILED (cannot mkfs test loop image)"
		exit 1
	fi
	mount -o loop ${IMG} ${MNT}
	if [ $? -ne 0 ]; then
		echo "FAILED (cannot mount test loop image)"
		rmdir ${MNT}
		rm -f ${IMG}
		exit 1
	fi
}

umount_loopback()
{
	cd ${START_DIR}
	umount -f ${MNT}
	rmdir ${MNT}
	rm -f ${IMG}
}

check()
{
	if [ $1 -eq 0 ]; then
		echo "PASSED ($2)"
		inc_passed
	else
		echo "FAILED ($2)"
		inc_failed
	fi
}

test_kernel_configs()
{
	configs="CONFIG_BLK_DEV_IO_TRACE"
	for c in $configs
	do
		grep "$c=y" /boot/config-$(uname -r) >& /dev/null
		check $? "$c=y in /boot/config-$(uname -r)"
	done
}

#
#  This test just performs a simple sanity check to see if
#  blktrace and blkparse can gather and parse the event data.
#  It does not sanity check the events.  Also, we have a very
#  low threshold of the number of events to check for as we
#  are just interested in the fact that *some* event data is
#  available.
#
test_dd_trace()
{
	echo ""
	echo "Test regime:"
	echo "  dd performing ${COUNT} 1K block writes"
	echo "  looking for at least ${EVENTS} blktrace events"
	#
	# flush out cache so we don't interfere with test
	#
	sync
	echo 3 > /proc/sys/vm/drop_caches

	#
	# kick off blktrace
	#
	echo ""
	echo "$(date): blktrace starting"
	blktrace -d $DEV -o - > $TMPFILE &
	pid=$!
	echo "$(date): dd starting"
	dd if=/dev/urandom of=test.dat bs=1024 conv=sync oflag=direct count=${COUNT} >& /dev/null
	sync
	echo 3 > /proc/sys/vm/drop_caches
	dd if=test.dat iflag=direct of=/dev/null bs=1024 >& /dev/null
	sync
	echo 3 > /proc/sys/vm/drop_caches
	ticks=0
	echo "$(date): dd stopped"

	#
	# Wait for blktrace to do it's thing.. Zzzz
	#
	echo "$(date): waiting for $DURATION seconds"
	while [ $ticks -lt $DURATION ]
	do
		sleep 1
		if [ ! -d /proc/$pid ];
		then
			break
		fi
		ticks=$((ticks + 1))
	done

	#
	# most of the time blktrace should still be running
	# so terminate and wait
	#
	if [ -d /proc/$pid ]; then
		echo "$(date): blktrace being terminated"
		kill -SIGINT $pid
		wait $pid
		echo "$(date): blktrace terminated"
	else
		echo "$(date): blktrace terminated prematurely"
	fi

	cat $TMPFILE | blkparse -i - > ${TMPFILE}.parsed
	echo "$(date): blktrace data parsed"
	echo ""

	dd_count=$(grep "dd" ${TMPFILE}.parsed | wc -l)
	rd=$(grep "Reads Completed:" ${TMPFILE}.parsed | tail -1 | awk '{ print $3 + 0 }')
	wr=$(grep "Writes Completed:" ${TMPFILE}.parsed | tail -1 | awk '{ print $7 + 0 }')

	#
	# really simple sanity checks on blktrace output, the format may
	# change so I don't want to perform too many complex sanity checks
	#
	if [ -z "$dd_count" ]; then
		dd_count=0
	fi
	if [ $dd_count -lt ${EVENTS} ]; then
		inc_failed
		echo "FAILED (expecting at least ${EVENTS} block traces events from the dd process, got $dd_count)"
	else
		inc_passed
		echo "PASSED (got $dd_count block trace events)"
	fi

	if [ -z "$rd" ]; then
		rd=0
	fi
	if [ $rd -lt ${EVENTS} ]; then
		inc_failed
		echo "FAILED (expecting at least ${EVENTS} block read traces events, got $rd)"
	else
		inc_passed
		echo "PASSED (got $rd block read trace events)"
	fi

	if [ -z "$wr" ]; then
		wr=0
	fi
	if [ $wr -lt ${EVENTS} ]; then
		inc_failed
		echo "FAILED (expecting at least ${EVENTS} block write traces events, got $wr)"
	else
		inc_passed
		echo "PASSED (got $wr block write trace events)"
	fi
	rm -rf $TMPFILE ${TMPFILE}.parsed
}


test_kernel_configs

which blktrace >& /dev/null
if [ $? -ne 0 ]; then
	echo "FAILED (cannot find blktrace tool, it is not installed)"
	exit 1
fi

mount_debugfs
mount_loopback

cd ${MNT}
get_dev $(pwd)

#
# sys/kernel/debug/tracing should exist
#
if [ ! -d /sys/kernel/debug/tracing ]; then
	echo "FAILED (/sys/kernel/debug/tracing does not exist)"
	umount_debugfs
	cd ${START_DIR}
	umount_loopback
	exit 1
fi

rc=0
test_dd_trace

cd ${START_DIR}

echo ""
echo "Summary: $passed passed, $failed failed"
echo ""

umount_loopback
umount_debugfs

exit $rc
