#!/bin/bash
cat << EOF
fix 5588383ece6127909df5b9d601d562fe5b9fe38a

    Btrfs: fix crash when mounting raid5 btrfs with missing disks

    The reproducer is

    $ mkfs.btrfs D1 D2 D3 -mraid5
    $ mkfs.ext4 D2 && mkfs.ext4 D3
    $ mount D1 /btrfs -odegraded

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

mkfs.btrfs -f -draid5 $DEV0 $DEV1 $DEV2 >& /dev/null
if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
	echo "mkfs.btrfs -f -draid5 $DEV0 $DEV1 $DEV2 failed"
	exit 1
fi

mkfs.ext4 -F $DEV1 >& /dev/null
mkfs.ext4 -F $DEV2 >& /dev/null

#
# mount: expect it to fail
#
mount -o degraded $DEV0 $MNT
if [ $? -eq 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
	echo "expecting mount $DEV $MNT to fail and it did not"
	exit 1
fi
rc=0
n=$(dmesg | grep "BUG" | wc -l)
if [ $n -gt 0 ]; then
	echo "mount failed, kernel bug:"
	dmesg
	umount $MNT >& /dev/null
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
