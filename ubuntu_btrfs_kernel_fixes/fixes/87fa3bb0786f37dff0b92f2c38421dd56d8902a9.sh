#!/bin/bash
cat << EOF
fix 87fa3bb0786f37dff0b92f2c38421dd56d8902a

    Btrfs: fix regression of btrfs device replace

    Commit 49c6f736f34f901117c20960ebd7d5e60f12fcac(
    btrfs: dev replace should replace the sysfs entry) added the missing sysfs entry
    in the process of device replace, but didn't take missing devices into account,
    so now we have

    BUG: unable to handle kernel NULL pointer dereference at 0000000000000088
    IP: [<ffffffffa0268551>] btrfs_kobj_rm_device+0x21/0x40 [btrfs]
    ...

    To reproduce it,
    1. mkfs.btrfs -f disk1 disk2
    2. mkfs.ext4 disk1
    3. mount disk2 /mnt -odegraded
    4. btrfs replace start -B 1 disk3 /mnt

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img
TMPIMG2=$TMP/test2.img

truncate --size 2G $TMPIMG0
truncate --size 2G $TMPIMG1
truncate --size 2G $TMPIMG2

DEV0=`losetup -f`
losetup $DEV0 $TMPIMG0

DEV1=`losetup -f`
losetup $DEV1 $TMPIMG1

DEV2=`losetup -f`
losetup $DEV2 $TMPIMG2

dmesg -c > /dev/null

mkfs.btrfs -f -m raid1 $DEV0 $DEV1 >& /dev/null
if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
	echo "mkfs.btrfs -f $DEV0 $DEV1 failed"
	exit 1
fi

#
# Trash dev0
#
mkfs.ext4 -F /dev/$DEV0

mount $DEV1 $MNT -odegraded
if [ $? -ne 0 ]; then
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
	echo "mount $DEV $MNT failed"
	exit 1
fi

btrfs replace start -f -B $DEV1 $DEV2 $MNT

n=$(dmesg | grep "BUG:" | wc -l)
rc=0
if [ $n -gt 0 ]; then
	echo "Kernel BUG found:"
	dmesg
	rc=1
fi

umount $MNT
losetup -d $DEV0
losetup -d $DEV1
losetup -d $DEV2
rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
exit $rc
