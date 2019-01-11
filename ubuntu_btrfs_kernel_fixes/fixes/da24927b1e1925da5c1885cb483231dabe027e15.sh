#!/bin/bash
cat << EOF
fix da24927b1e1925da5c1885cb483231dabe027e15

    Btrfs: get write access when removing a device

    Steps to reproduce:
     # mkfs.btrfs -d single -m single <disk0> <disk1>
     # mount -o ro <disk0> <mnt0>
     # mount -o ro <disk0> <mnt1>
     # mount -o remount,rw <mnt0>
     # umount <mnt0>
     # btrfs device delete <disk1> <mnt1>

    We can remove a device from a R/O filesystem. The reason is that we just check
    the R/O flag of the super block object. It is not enough, because the kernel
    may set the R/O flag only for the mount point. We need invoke

        mnt_want_write_file()

    to do a full check.

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img

truncate --size 512M $TMPIMG0
truncate --size 512M $TMPIMG1

DEV0=`losetup -f`
losetup $DEV0 $TMPIMG0

DEV1=`losetup -f`
losetup $DEV1 $TMPIMG1

mkfs.btrfs -f -d single -m single $DEV0 $DEV1 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f -d single -m single $DEV0 $DEV1 failed"
	losetup -d $DEV0
	losetup -d $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	exit 1
fi

mkdir $MNT/mnt0
mkdir $MNT/mnt1

mount -o ro $DEV0 $MNT/mnt0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount -o ro $DEV0 $MNT/mnt0 failed"
	losetup -d $DEV0
	losetup -d $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	rmdir $MNT/mnt0 $MNT/mnt1
	exit 1
fi

mount -o ro $DEV0 $MNT/mnt1 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount -o ro $DEV0 $MNT/mnt1 failed"
	losetup -d $DEV0
	losetup -d $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	rmdir $MNT/mnt0 $MNT/mnt1
	exit 1
fi

mount -o remount,rw $MNT/mnt0
umount $MNT/mnt0
echo "Attempting to delete a read-only file system, this is not allowed."
btrfs device delete $DEV1 $MNT/mnt1
rc=$?
if [ $rc -eq 0 ]; then
	echo "Managed to delete a read-only file system, this is a test failure"
	rc=1
else
	rc=0
fi

umount $MNT/mnt1 >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
rmdir $MNT/mnt0 $MNT/mnt1
exit $rc
