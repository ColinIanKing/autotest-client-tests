#!/bin/bash
cat << EOF
fix 2365dd3ca02bbb6d3412404482e1d85752549953

btrfs: undo sysfs when open_ctree() fails

    reproducer:
    mkfs.btrfs -f /dev/sdb &&\
    mount /dev/sdb /btrfs &&\
    btrfs dev add -f /dev/sdc /btrfs &&\
    umount /btrfs &&\
    wipefs -a /dev/sdc &&\
    mount -o degraded /dev/sdb /btrfs
    //above mount fails so try with RO
    mount -o degraded,ro /dev/sdb /btrfs

    ------
    sysfs: cannot create duplicate filename '/fs/btrfs/3f48c79e-5ed0-4e87-b189-86e749e503f4'
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

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 >& /dev/null failed"
	losetup -d $DEV0
	rm $TMPIMG0
	exit 1
fi

mount $DEV0 $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT failed"
	losetup -d $DEV0 $DEV1
	rm $TMPIMG0 $TMPIMG1
	exit 1
fi

btrfs dev add -f $DEV1 $MNT
if [ $? -ne 0 ]; then
	echo "btrfs dev add -f $DEV1 $MNT failed"
	losetup -d $DEV0 $DEV1
	rm $TMPIMG0 $TMPIMG1
	exit 1
fi

umount $MNT
if [ $? -ne 0 ]; then
	echo "umount $MNT failed"
	umount $MNT
	losetup -d $DEV0 $DEV1
	rm $TMPIMG0 $TMPIMG1
	exit 1
fi

wipefs -a $DEV1 >& /dev/null

#
# Following will fail:
#
mount -o degraded $DEV0 $MNT >& /dev/null
if [ $? -eq 0 ]; then
	echo "mount -o degraded $DEV0 $MNT was expected to fail"
	umount $MNT
	losetup -d $DEV0 $DEV1
	rm $TMPIMG0 $TMPIMG1
	exit 1
fi

#
# The following should work:
#
dmesg -c > /dev/null
mount -o degraded,ro $DEV0 $MNT
if [ $? -ne 0 ]; then
	echo "mount -o degraded,ro $DEV0 $MNT failed"
	losetup -d $DEV0 $DEV1
	rm $TMPIMG0 $TMPIMG1
	exit 1
fi
umount $MNT

dumped=$(dmesg | grep "dump_stack" | wc -l)
if [ $dumped -gt 0 ]; then
	echo "found a kernel stack dump"
	dmesg
	losetup -d $DEV0 $DEV1
	rm $TMPIMG0 $TMPIMG1
	exit 1
fi

#
#  the following should not hang:
#
modprobe -s btrfs
modprobe btrfs

losetup -d $DEV0 $DEV1
rm $TMPIMG0 $TMPIMG1
exit $rc
