#!/bin/bash
cat << EOF
fix f63e0cca9174dd8b47380f61565ab7b921d6ac2c

    btrfs: ignore device open failures in __btrfs_open_devices

    This:

       # mkfs.btrfs /dev/sdb{1,2} ; wipefs -a /dev/sdb1; mount /dev/sdb2 /mnt/test

    would lead to a blkdev open/close mismatch when the mount fails, and
    a permanently busy (opened O_EXCL) sdb2:

       # wipefs -a /dev/sdb2
       wipefs: error: /dev/sdb2: probing initialization failed: Device or resource busy

    It's because btrfs_open_devices() may open some devices, fail on
    the last one, and return that failure stored in "ret."   The mount
    then fails, but the caller then does not clean up the open devices.

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img
DEV0=/dev/loop0
DEV1=/dev/loop1

truncate --size 1G $TMPIMG0
truncate --size 1G $TMPIMG1

losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1

mkfs.btrfs -f $DEV{0,1} >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 failed"
	losetup -d $DEV0
	losetup -d $DEV1
	rm $TMPIMG0 $TMPIMG1
	exit 1
fi

wipefs -a $DEV0

mount $DEV1 $MNT >& /dev/null
if [ $? -eq 0 ]; then
	echo "mount $DEV1 $MNT should have failed"
	losetup -d $DEV0
	losetup -d $DEV1
	rm $TMPIMG0 $TMPIMG1
	exit 1
fi
wipefs -a $DEV1
rc=$?
if [ $rc -ne 0 ]; then
	echo "wipefs should not fail"
	rc=1
else
	rc=0
fi

umount $MNT >& /dev/null
losetup -d $DEV0
losetup -d $DEV1
rm $TMPIMG0 $TMPIMG1
exit $rc
