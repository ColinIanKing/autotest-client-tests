#!/bin/bash
cat << EOF
fix 198605a8e2077f174c9834c97b836f535e4e56dd

    Btrfs: get write access when doing resize fs

    Steps to reproduce:
     # mkfs.btrfs <partition>
     # mount -o ro <partition> <mnt0>
     # mount -o ro <partition> <mnt1>
     # mount -o remount,rw <mnt0>
     # umount <mnt0>
     # btrfs fi resize 10g <mnt1>

    We re-sized a R/O filesystem. The reason is that we just check the R/O flag
    of the super block object. It is not enough, because the kernel may set the
    R/O flag only for the mount point. We need invoke mnt_want_write_file() to
    do a full check.

EOF

TMPIMG0=$TMP/test0.img

DEV0=`losetup -f`

truncate --size 512M $TMPIMG0

losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs $DEV0 failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

mkdir $MNT/mnt0
mkdir $MNT/mnt1

mount -o ro $DEV0 $MNT/mnt0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount -o ro $DEV0 $MNT/mnt0 failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	rmdir $MNT/mnt0 $MNT/mnt1
	exit 1
fi

mount -o ro $DEV0 $MNT/mnt1 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount -o ro $DEV0 $MNT/mnt1 failed"
	umount $MNT/mnt0
	losetup -d $DEV0
	rm -f $TMPIMG0
	rmdir $MNT/mnt0 $MNT/mnt1
	exit 1
fi

mount -o remount,rw $MNT/mnt0
umount $MNT/mnt0
echo "Attempting to resize a read-only file system, this is not allowed."
btrfs fi resize 768M $MNT/mnt1
rc=$?
if [ $rc -eq 0 ]; then
	echo "Managed to resize a read-only file system, this is a test failure"
	rc=1
else
	rc=0
fi

umount $MNT/mnt1 >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
rmdir $MNT/mnt0 $MNT/mnt1
exit $rc
