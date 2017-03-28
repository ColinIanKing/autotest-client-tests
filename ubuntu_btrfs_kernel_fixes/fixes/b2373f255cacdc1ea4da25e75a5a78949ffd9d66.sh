#!/bin/bash
cat << EOF
fix b2373f255cacdc1ea4da25e75a5a78949ffd9d66

    btrfs: create sprout should rename fsid on the sysfs as well

    Creating sprout will change the fsid of the mounted root.
    do the same on the sysfs as well.

    reproducer:
     mount /dev/sdb /btrfs (seed disk)
     btrfs dev add /dev/sdc /btrfs
     mount -o rw,remount /btrfs
     btrfs dev del /dev/sdb /btrfs
     mount /dev/sdb /btrfs

    Error:
    kobject_add_internal failed for fe350492-dc28-4051-a601-e017b17e6145 with -EEXIST, don't try to register things with the same name in the same directory.

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img

DEV0=/dev/loop0
DEV1=/dev/loop1

truncate --size 2G $TMPIMG0
truncate --size 2G $TMPIMG1

losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	echo "mkfs.btrfs -f $DEV0 $MNT failed"
	exit 1
fi

mount $DEV0 $MNT
btrfs dev add -f $DEV1 $MNT
mount -o rw,remount $MNT
btrfs dev del $DEV0 $MNT
mount $DEV0 $MNT
if [ $? -eq 0 ]; then
	umount $MNT
	losetup -d $DEV0
	losetup -d $DEV1
	echo "mount $DEV0 /mnt was meant to fail"
	exit 1
fi

umount $MNT
losetup -d $DEV0
losetup -d $DEV1
rm -f $TMPIMG0 $TMPIMG1
exit 0
