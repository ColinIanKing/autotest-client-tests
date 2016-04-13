#!/bin/sh

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

rm -rf $IMG $MNT

which mksquashfs > /dev/null
if [ $? -ne 0 ]; then
	echo "SKIPPED: mksquashfs is not installed, aborting test"
	exit 0
fi

mksquashfs $SRC $IMG -no-progress > /dev/null
if [ $? -ne 0 ]; then
	echo "SKIPPED: mksquashfs failed, aborting test"
	exit 0
fi

mkdir -p $MNT
echo -n "Testing mount of squashfs: "
mount $IMG $MNT -t squashfs -o loop
if [ $? -ne 0 ]; then
	echo "FAILED"
	exit 1
fi
echo "PASSED"

echo -n "Testing umount of squashfs: "
umount $MNT
if [ $? -ne 0 ]; then
	echo "FAILED"
	exit 1
fi
echo "PASSED"

echo -n "Checking data integrity: "
mount $IMG $MNT -t squashfs -o loop
if [ $? -ne 0 ]; then
	echo "FAILED (remount)"
	exit 1
fi
HERE=$(pwd)
cd $SRC
diffs=$(find . -exec diff {} $MNT/{} \; 2>&1 | wc -l)
cd $HERE
umount $MNT
if [ $? -ne 0 ]; then
	echo "FAILED (umount)"
	exit 1
fi
if [ $diffs -ne 0 ]; then
	echo "FAILED (squashed $SRC different from original $SRC)"
	exit 1
fi
echo "PASSED"

rm -rf $IMG $MNT
exit 0
