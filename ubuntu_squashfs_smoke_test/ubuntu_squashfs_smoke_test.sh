#!/bin/bash

#
# Copyright (C) 2016 Canonical
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
#  Trival "smoke test" squashfs tests just to see
#  if very basic functionality works, that is mounting
#  and umounting, and data integrity check
#
SRC=/bin
IMG=/tmp/squashfs.sqsh
MNT=/tmp/squashfs-mnt

#
# From 4.4 onwards let's test every compression method that
# squashfs supports
#
read major minor rest < <(uname -r | tr '.' ' ')
if (( $(echo "$major.$minor >= 4.4" | bc -l) )); then
	COMP="gzip lzo xz"
else
	COMP="gzip lzo xz"
fi

#
# 2.4 kernels upwards support lazy umount
#
if (( $(echo "$major.$minor >= 2.4" | bc -l) )); then
	lazy="-l"
else
	lazy=""
fi

rm -rf $IMG $MNT

which mksquashfs > /dev/null
if [ $? -ne 0 ]; then
	echo "SKIPPED: mksquashfs is not installed, aborting test"
	exit 0
fi

for comp in $COMP
do
	echo "Testing with compression method $comp"
	mksquashfs $SRC $IMG -no-progress -comp $comp > /dev/null
	if [ $? -ne 0 ]; then
		echo "SKIPPED: mksquashfs failed, aborting test"
		exit 0
	fi

	mkdir -p $MNT
	echo -n "Testing mount of squashfs: "
	mount $IMG $MNT -t squashfs -o loop
	if [ $? -ne 0 ]; then
		echo "FAILED ($comp)"
		exit 1
	fi
	echo "PASSED ($comp)"

	echo -n "Testing umount of squashfs: "
	#
	#  Need to retry because sometimes
	#  daemons try to scan newly mounted file
	#  systems making it impossible to umount
	#
	retry=0
	while [ $retry -lt 10 ]
	do
		umount $MNT $lazy
		ret=$?
		if [ $ret -eq 0 ]; then
			break
		fi
		retry=$((retry + 1))
		sleep 1
	done
	if [ $ret -ne 0 ]; then
		echo "FAILED (umount, $comp)"
		exit 1
	fi
	echo "PASSED ($comp)"

	echo -n "Checking data integrity: "
	mount $IMG $MNT -t squashfs -o loop
	if [ $? -ne 0 ]; then
		echo "FAILED (remount, $comp)"
		exit 1
	fi
	HERE=$(pwd)
	cd $SRC
	diffs=$(find . -exec diff {} $MNT/{} \; 2>&1 | wc -l)
	cd $HERE
	#
	#  Need to retry because sometimes
	#  daemons try to scan newly mounted file
	#  systems making it impossible to umount
	#
	retry=0
	while [ $retry -lt 10 ]
	do
		umount $MNT $lazy
		ret=$?
		if [ $ret -eq 0 ]; then
			break
		fi
		retry=$((retry + 1))
		sleep 1
	done
	if [ $ret -ne 0 ]; then
		echo "FAILED (umount, $comp)"
		exit 1
	fi

	if [ $diffs -ne 0 ]; then
		echo "FAILED (squashed $SRC different from original $SRC, $comp)"
		exit 1
	fi
	echo "PASSED ($comp)"
	rm -rf $IMG $MNT
done

exit 0
