#!/bin/bash
cat << EOF
fix e755f780865221252ef3321215c9796b78e7b1c5

    btrfs: fix null pointer dereference in clone_fs_devices when name is null

    when one of the device path is missing btrfs_device name is null. So this
    patch will check for that.

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img
TMPIMG2=$TMP/test2.img
TMPIMG3=$TMP/test3.img

DEV0=/dev/loop0
DEV1=/dev/loop1
DEV2=/dev/loop2

truncate --size 2G $TMPIMG0
truncate --size 2G $TMPIMG1
truncate --size 2G $TMPIMG2

losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1
losetup $DEV2 $TMPIMG2

dmesg -c > /dev/null

mkfs.btrfs -f -draid1 $DEV0 $DEV1 >& /dev/null
if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
	echo "mkfs.btrfs -f $DEV0 $DEV1 failed"
	exit 1
fi

btrfstune -S 1 $DEV0
modprobe -r btrfs && modprobe btrfs

mount -o degraded $DEV0 $MNT
if [ $? -ne 0 ]; then
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
	echo "mount $DEV $MNT failed"
	exit 1
fi

btrfs dev add $DEV2 $MNT
rc=0
n=$(dmesg | grep "BUG" | wc -l)
if [ $n -gt 0 ]; then
	echo "mount failed, kernel bug:"
	dmesg
	umount $MNT
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
	rc=1
fi

umount $MNT
losetup -d $DEV0
losetup -d $DEV1
losetup -d $DEV2
rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
exit $rc
