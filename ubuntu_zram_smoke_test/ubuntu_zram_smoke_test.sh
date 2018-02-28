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
# Author: Colin Ian King
#

#
#  Trival "smoke test" ZRAM tests just to see
#  if very basic functionality work
#

zram_load()
{
	LOADED=0
	n=$(cat /proc/modules | grep zram | wc -l)
	if [ $n -eq 0 ]; then
		modprobe zram
		if [ $? -ne -0 ]; then
			echo "FAILED: cannot load zram module"
			exit 1
		fi
		echo "PASSED: zram module loaded"
		LOADED=1
	fi
}

zram_unload()
{
	sleep 1
	if [ $LOADED -eq 1 ]; then
		modprobe -r zram
		if [ $? -ne -0 ]; then
			echo "FAILED: cannot unload zram module"
			exit 1
		fi
		echo "PASSED: zram module unloaded"
	fi
}

zram_test_compression_streams()
{
	#
	# Older kernels don't support the max_comp_streams feature
	#
	if [ -e /sys/block/zram0/max_comp_streams ]; then
		n=$(cat /sys/block/zram0/max_comp_streams)
		if [ $n -lt 1 ]; then
			echo "FAILED: got $n compression streams, expecting at least 1"
			zram_unload
			exit 1
		else
			echo "PASSED: got $n compression streams"
		fi
	fi
}

zram_test_compression_algorithms()
{
	#
	# Older kernels don't support the comp_algorithm feature
	#
	if [ -e /sys/block/zram0/comp_algorithm ]; then
		ALGORITHMS=$(cat /sys/block/zram0/comp_algorithm)
		if [ -z "$ALGORITHMS" ]; then
			echo "FAIL: got NO compression algorithms"
			zram_unload
			exit 1
		fi
		ALGORITHMS=$(echo $ALGORITHMS | sed 's/\]//' | sed 's/\[//')
		echo "PASSED: got $ALGORITHMS compression algorithmns"
	else
		ALGORITHMS="default"
	fi
}

zram_test_ext4()
{
	sleep 1
	echo 1 > /sys/block/zram0/reset
	sleep 1
	#
	# Older kernels don't support the comp_algorithm feature
	#
	if [ "$1" != "default" ]; then
		echo $1 > /sys/block/zram0/comp_algorithm
	fi
	echo 128M > /sys/block/zram0/disksize
	mnt=$(pwd)/mnt
	mkdir -p $mnt

	mkfs.ext4 -F /dev/zram0 >& /dev/null
	if [ $? -ne 0 ]; then
		echo "FAILED: mkfs.ext4 on ZRAM unsuccessful ($1)"
		zram_unload
		exit 1
	fi
	echo "PASSED: mkfs.ext4 on ZRAM successful"

	mount /dev/zram0 $mnt
	if [ $? -ne 0 ]; then
		echo "FAILED: ext4 mount on ZRAM unsuccessful ($1)"
		zram_unload
		exit 1
	fi

	dd if=/dev/urandom of=$mnt/test bs=1M count=40 >& /dev/null
	sync
	if [ $? -ne 0 ]; then
		echo "FAILED: dd of 40MB to 128MB ZRAM ext4 filesystem unsuccessful ($1)"
		zram_unload
		exit 1
	fi

	if [ -e /sys/block/zram0/mm_stat ]; then
		used1=$(cat /sys/block/zram0/mm_stat | awk '{print $2}')
	else
		#
		# Older kernels don't support the mm_stat feature
		#
		used1="unknown"
	fi
	rm $mnt/test
	sync
	dd if=/dev/zero of=$mnt/test bs=1M count=40 >& /dev/null
	sync

	#
	#  Try and compact the memory
	#
	if [ -e /sys/block/zram0/compact ]; then
		#
		# Older kernels don't support the compact feature
		#
		echo 1 > /sys/block/zram0/compact
	fi

	if [ -e /sys/block/zram0/mm_stat ]; then
		used2=$(cat /sys/block/zram0/mm_stat | awk '{print $2}')
	else
		#
		# Older kernels don't support the mm_stat feature
		#
		used2="unknown"
	fi

	umount /dev/zram0
	if [ $? -ne 0 ]; then
		echo "FAILED: ext4 unmount on ZRAM unsuccessful ($1)"
		zram_unload
		exit 1
	fi
	sleep 1
	echo "PASSED: ext4 on ZRAM ($1), memory used: $used1 $used2"
	rm -rf $mnt
}

zram_load
zram_test_compression_streams
zram_test_compression_algorithms

for algo in $ALGORITHMS
do
	zram_test_ext4 $algo
done

zram_unload

echo "PASSED: ALL TESTS"

exit 0
