#!/bin/bash
cat << EOF
fix 671415b7db49f62896f0b6d50fc4f312a0512983

    Btrfs: fix deadlock caused by the nested chunk allocation

    Steps to reproduce:
     # mkfs.btrfs -m raid1 <disk1> <disk2>
     # btrfstune -S 1 <disk1>
     # mount <disk1> <mnt>
     # btrfs device add <disk3> <disk4> <mnt>
     # mount -o remount,rw <mnt>
     # dd if=/dev/zero of=<mnt>/tmpfile bs=1M count=1
     Deadlock happened.

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img
TMPIMG2=$TMP/test2.img
TMPIMG3=$TMP/test3.img

DEV0=/dev/loop0
DEV1=/dev/loop1
DEV2=/dev/loop2
DEV3=/dev/loop3

truncate --size 1G $TMPIMG0
truncate --size 1G $TMPIMG1
truncate --size 1G $TMPIMG2
truncate --size 1G $TMPIMG3

losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1
losetup $DEV2 $TMPIMG2
losetup $DEV3 $TMPIMG3

mkfs.btrfs -f -m raid1 $DEV0 $DEV1
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f -m raid 1 $DEV0 $DEV1 failed"
	losetup -d $DEV0 $DEV1 $DEV2 $DEV3
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2 $TMPIMG3
	exit 1
fi

btrfstune -S 1 $DEV0
if [ $? -ne 0 ]; then
	echo "btrfstune -S 1 $DEV0 failed"
	losetup -d $DEV0 $DEV1 $DEV2 $DEV3
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2 $TMPIMG3
	exit 1
fi

mount $DEV0 $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT failed"
	losetup -d $DEV0 $DEV1 $DEV2 $DEV3
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2 $TMPIMG3
	exit 1
fi

btrfs device add $DEV2 $DEV3 $MNT
if [ $? -ne 0 ]; then
	echo "btrfs device add $DEV2 $DEV3 $MNT failed"
	losetup -d $DEV0 $DEV1 $DEV2 $DEV3
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2 $TMPIMG3
	exit 1
fi

mount -o remount,rw $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount -o remount,rw $MNT >& /dev/null failed"
	losetup -d $DEV0 $DEV1 $DEV2 $DEV3
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2 $TMPIMG3
	exit 1
fi
dd if=/dev/zero of=$MNT/tmpfile bs=1M count=1 >& /dev/null
rc=$?
if [ $rc -ne 0 ]; then
    echo "dd command didn't trigger the deadlock, but failed with another reason"
fi

umount $MNT
losetup -d $DEV0 $DEV1 $DEV2 $DEV3
rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2 $TMPIMG3
exit $rc
