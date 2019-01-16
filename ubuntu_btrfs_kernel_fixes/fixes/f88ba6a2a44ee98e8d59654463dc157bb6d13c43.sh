#!/bin/bash
cat << EOF
fix f88ba6a2a44ee98e8d59654463dc157bb6d13c43

    Btrfs: skip submitting barrier for missing device

    I got an error on v3.13:
     BTRFS error (device sdf1) in write_all_supers:3378: errno=-5 IO failure (errors while submitting device barriers.)

    how to reproduce:
      > mkfs.btrfs -f -d raid1 /dev/sdf1 /dev/sdf2
      > wipefs -a /dev/sdf2
      > mount -o degraded /dev/sdf1 /mnt
      > btrfs balance start -f -sconvert=single -mconvert=single -dconvert=single /mnt

    The reason of the error is that barrier_all_devices() failed to submit
    barrier to the missing device.  However it is clear that we cannot do
    anything on missing device, and also it is not necessary to care chunks
    on the missing device.

    This patch stops sending/waiting barrier if device is missing.

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img

truncate --size 1G $TMPIMG0
truncate --size 1G $TMPIMG1

DEV0=`losetup -f`
losetup $DEV0 $TMPIMG0

DEV1=`losetup -f`
losetup $DEV1 $TMPIMG1

mkfs.btrfs -f -d raid1 $DEV0 $DEV1 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 failed"
	losetup -d $DEV0
	losetup -d $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	exit 1
fi

sync
wipefs -a $DEV1 >& /dev/null
rc=0
dmesg -c > /dev/null
mount -o degraded $DEV0 $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount -o degraded $DEV0 $MNT was expected to pass"
	exit 1
fi
btrfs balance start -f -sconvert=single -mconvert=single -dconvert=single $MNT >& /dev/null
n=$(dmesg | grep "BTRFS error (device loop0) in write_all_supers" | wc -l)
if [ $n -gt 0 ]; then
	echo "failed: found btrfs error: BTRFS error (device loop0) in write_all_supers"
	rc=1
fi
n=$(dmesg | grep "WARNING" | wc -l)
if [ $n -gt 0 ]; then
	echo "failed: found kernel WARNING"
	dmesg
	rc=1
fi

umount $DEV0 >& /dev/null
losetup -d $DEV0
losetup -d $DEV1
rm -f $TMPIMG0 $TMPIMG1
exit $rc
