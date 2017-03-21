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

passed=0
failed=0

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
	DEV=$(df $mount | grep dev | head -1 | cut -d' ' -f1 | sed 's/[0-9]//g')
	if [ -z "$DEV" ]; then
		echo "SKIPPED cannot determine block device $1 is located on (skipping test)"
		exit 0
	else
		echo "Using block device $DEV for path $1"
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

test_dd_trace()
{
	blktrace -d $DEV -o - > $TMPFILE &
	pid=$!
	dd if=/dev/urandom of=test.dat bs=1024 conv=sync oflag=direct count=2048 >& /dev/null
	sync
	echo 3 > /proc/sys/vm/drop_caches
	dd if=test.dat iflag=direct of=/dev/null bs=1024 >& /dev/null
	sync
	echo 3 > /proc/sys/vm/drop_caches
	sleep 1
	kill -SIGINT $pid
	cat $TMPFILE | blkparse -i - > ${TMPFILE}.parsed

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
	if [ $dd_count -lt 1024 ]; then
		inc_failed
		echo "FAILED expecting at least 1024 block traces events from the dd process, got $dd_count"
	else
		inc_passed
		echo "PASSED got $dd_count block trace events"
	fi

	if [ -z "$rd" ]; then
		rd=0
	fi
	if [ $rd -lt 1024 ]; then
		inc_failed
		echo "FAILED expecting at least 1024 block read traces events, got $rd"
	else
		inc_passed
		echo "PASSED got $rd block read trace events"
	fi

	if [ -z "$wr" ]; then
		wr=0
	fi
	if [ $wr -lt 1024 ]; then
		inc_failed
		echo "FAILED expecting at least 1024 block write traces events, got $wr"
	else
		inc_passed
		echo "PASSED got $wr block write trace events"
	fi
	rm -rf $TMPFILE ${TMPFILE}.parsed
}


test_kernel_configs

which blktrace >& /dev/null
if [ $? -ne 0 ]; then
	echo "FAILED cannot find blktrace tool, it is not installed"
	exit 1
fi

mount_debugfs
get_dev $(pwd)

#
# sys/kernel/debug/tracing should exist
#
if [ ! -d /sys/kernel/debug/tracing ]; then
	echo "FAILED /sys/kernel/debug/tracing does not exist"
	umount_debugfs
	exit 1
fi

rc=0
test_dd_trace

echo "Summary: $passed passed, $failed failed"

umount_debugfs

exit $rc
