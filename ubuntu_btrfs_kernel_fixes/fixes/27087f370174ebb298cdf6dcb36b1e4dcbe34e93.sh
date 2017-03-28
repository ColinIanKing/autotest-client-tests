#!/bin/bash
cat << EOF
fix 27087f370174ebb298cdf6dcb36b1e4dcbe34e93

    Btrfs: init device stats for new devices

    Device stats are only initialized (read from tree items) on mount.
    Trying to read device stats after adding or replacing new devices will
    return errors.

    btrfs_init_new_device() and btrfs_init_dev_replace_tgtdev() are the two
    functions that allocate and initialize new btrfs_device structures after
    a filesystem is mounted. They set the device stats to zero by using
    kzalloc() which is correct for new devices. The only missing thing was
    to declare these stats as being valid (device->dev_stats_valid = 1) and
    this patch adds this missing code.

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img
TMPIMG2=$TMP/test2.img
DEV0=/dev/loop0
DEV1=/dev/loop1
DEV2=/dev/loop2

truncate --size 512M $TMPIMG0
truncate --size 512M $TMPIMG1
truncate --size 512M $TMPIMG2
losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1
losetup $DEV2 $TMPIMG2

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs $DEV0 failed"
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
	exit 1
fi

mount $DEV0 $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT failed"
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
	exit 1
fi

rc=0
btrfs device add $DEV1 $MNT
n=$(btrfs device stat $MNT | awk '{ print $2}' | grep -v "0" | wc -l)
if [ $n -gt 0 ]; then
	echo "Found $n errors in first btrfs device stat check"
	rc=1
fi
btrfs replace start -B $DEV1 $DEV2 $MNT
n=$(btrfs device stat $MNT | awk '{ print $2}' | grep -v "0" | wc -l)
if [ $n -gt 0 ]; then
	echo "Found $n errors in second btrfs device stat check"
	rc=1
fi
umount $MNT

losetup -d $DEV0
losetup -d $DEV1
losetup -d $DEV2
rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
exit $rc
