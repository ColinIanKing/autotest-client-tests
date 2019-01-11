#!/bin/bash
cat << EOF
fix 4330e183c9537df20952d4a9ee142c536fb8ae54

btrfs: Do chunk level check for degraded rw mount

With this patch, we can mount in the following case:
 # mkfs.btrfs -f -m raid1 -d single /dev/sdb /dev/sdc
 # wipefs -a /dev/sdc
 # mount /dev/sdb /mnt/btrfs -o degraded
 As the single data chunk is only on sdb, so it's OK to mount as
 degraded, as missing one device is OK for RAID1.

But still fail in the following case as expected:
 # mkfs.btrfs -f -m raid1 -d single /dev/sdb /dev/sdc
 # wipefs -a /dev/sdb
 # mount /dev/sdc /mnt/btrfs -o degraded
 As the data chunk is only in sdb, so it's not OK to mount it as
 degraded.

This is a follow-up fix for:
  2365dd3ca02bbb6d3412404482e1d85752549953 (btrfs: undo sysfs when open_ctree() fails)
And should be tested on newer kernels.
  ::

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img

DEV0=/dev/loop0
DEV1=/dev/loop1

truncate --size 512M $TMPIMG0
truncate --size 512M $TMPIMG1

losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1

function cleanup {
    umount $MNT &> /dev/null
	losetup -d $DEV0 $DEV1
	rm -f $TMPIMG0 $TMPIMG1
}
trap cleanup EXIT

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 >& /dev/null failed"
	exit 1
fi

mount $DEV0 $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT failed"
	exit 1
fi

btrfs dev add -f $DEV1 $MNT
if [ $? -ne 0 ]; then
	echo "btrfs dev add -f $DEV1 $MNT failed"
	exit 1
fi

umount $MNT
if [ $? -ne 0 ]; then
	echo "umount $MNT failed"
	exit 1
fi

wipefs -a $DEV1 >& /dev/null

#
# Following will pass:
#
mount -o degraded $DEV0 $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount -o degraded $DEV0 $MNT was expected to pass"
	exit 1
fi

#
# Add $DEV1 back, remove the missing dev so it will become a complete RAID again
#
btrfs dev add -f $DEV1 $MNT
if [ $? -ne 0 ]; then
	echo "btrfs dev add -f $DEV1 $MNT to a degraded mount point has failed"
	exit 1
fi

btrfs device delete missing $MNT
if [ $? -ne 0 ]; then
	echo "btrfs device delete missing $MNT failed"
	exit 1
fi

#
# Destroy the first disk that contains data chunk
# Following should fail:
#
umount $MNT
if [ $? -ne 0 ]; then
	echo "umount $MNT failed"
	exit 1
fi

wipefs -a $DEV0 >& /dev/null

dmesg -c > /dev/null
mount -o degraded $DEV1 $MNT
if [ $? -eq 0 ]; then
	echo "mount -o degraded $DEV0 $MNT was expected to fail"
	exit 1
else
	echo "degraded mount failed as expected"
fi

dumped=$(dmesg | grep "dump_stack" | wc -l)
if [ $dumped -gt 0 ]; then
	echo "found a kernel stack dump"
	dmesg
	exit 1
fi
