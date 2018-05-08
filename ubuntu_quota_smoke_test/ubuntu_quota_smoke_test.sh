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
#  Trival "smoke test" quota tests just to see
#  if basic functionality works
#
TMPFILE=/tmp/quota-kernel-trace-$$.tmp

passed=0
failed=0

#
#  Loopback image and mount point, image is 33% larger than
#  file to be dd'd.
#
QUOTA_DIR=$(pwd)
IMG=${QUOTA_DIR}/loop.img
MNT=${QUOTA_DIR}/mnt
IMG_COUNT=1M
USR=$(whoami)

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

mount_loopback()
{
	mkdir -p ${MNT}
	dd if=/dev/zero of=${QUOTA_DIR}/loop.img bs=1K count=${IMG_COUNT} >& /dev/null
	mkfs.ext4 -F ${IMG} >& /dev/null
	if [ $? -ne 0 ]; then
		echo "FAILED (cannot mkfs test loop image)"
		exit 1
	fi
	mount -o loop -o usrquota,grpquota ${IMG} ${MNT}
	if [ $? -ne 0 ]; then
		echo "FAILED (cannot mount test loop image)"
		rmdir ${MNT}
		rm -f ${IMG}
		exit 1
	fi
}

umount_loopback()
{
	cd ${QUOTA_DIR}
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

#
#  This test just performs a simple sanity check to see if
#  quota and blkparse can gather and parse the event data.
#  It does not sanity check the events.  Also, we have a very
#  low threshold of the number of events to check for as we
#  are just interested in the fact that *some* event data is
#  available.
#
test_quota()
{
		quotacheck -vucmg ${MNT} &> /dev/null
		rc=$?
		check $rc "quotacheck -vucmg"
		if [ $rc -ne 0 ]; then
			return
		fi
		echo ""

		quotaon -v ${MNT}
		rc=$?
		check $rc "quotaon -v"
		if [ $rc -ne 0 ]; then
			return
		fi
		echo ""

		quotastats
		rc=$?
		check $rc "quotastats"
		if [ $rc -ne 0 ]; then
			return
		fi
		echo ""

		setquota -u ${USR} 10000 11000 1000 1100 ${MNT}
		rc=$?
		check $rc "setquota -u ${USR} 10000 12000 1000 1200 ${MNT}"
		if [ $rc -ne 0 ]; then
			return
		fi
		echo ""

		setquota -u -t 6000 6000 ${MNT}
		rc=$?
		check $rc "setquota -u -t 6000 6000 ${MNT}"
		if [ $rc -ne 0 ]; then
			return
		fi
		echo ""

		setquota -u -T ${USR} 1 1 ${MNT}
		rc=$?
		check $rc "setquota -u -T ${USR} 1 1 ${MNT}"
		if [ $rc -ne 0 ]; then
			return
		fi
		echo ""

		dd if=/dev/zero of=${MNT}/test bs=1M count=85 &> /dev/null

		repquota -a
		rc=$?
		check $rc "repquota -a"
		if [ $rc -ne 0 ]; then
			return
		fi
		echo ""

		warnquota -u
		rc=$?
		check $rc "warnquota -u"
		if [ $rc -ne 0 ]; then
			return
		fi
		echo ""

		quotaoff -v ${MNT}
		rc=$?
		check $rc "quotaoff -v"
		if [ $rc -ne 0 ]; then
			return
		fi
		echo ""
}

which quota >& /dev/null
if [ $? -ne 0 ]; then
	echo "FAILED (cannot find quota tool, it is not installed)"
	exit 1
fi

mount_loopback

cd ${MNT}
get_dev $(pwd)

rc=0
test_quota

cd ${QUOTA_DIR}

echo ""
echo "Summary: $passed passed, $failed failed"
echo ""

umount_loopback

exit $rc
