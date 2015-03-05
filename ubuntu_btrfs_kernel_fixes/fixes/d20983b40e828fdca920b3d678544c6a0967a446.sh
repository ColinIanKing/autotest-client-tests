#!/bin/bash
cat << EOF
fix 63dd86fa79db737a50f47488e5249f24e5acebc1

    btrfs: fix rw_devices miss match after seed replace

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img
TMPIMG2=$TMP/test2.img

DEV0=/dev/loop0
DEV1=/dev/loop1
DEV2=/dev/loop2

truncate --size 256M $TMPIMG0
truncate --size 256M $TMPIMG1
truncate --size 256M $TMPIMG2

losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1
losetup $DEV2 $TMPIMG2

if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	rm $TMPIMG0 $TMPIMG1 $TMPIMG2
	echo "mkfs.btrfs on $DEV failed"
	exit 1
fi
mkfs.btrfs -f -d raid1 -m raid1 $DEV0 $DEV1 >& /dev/null
btrfstune -S 1 $DEV0 >& /dev/null

mount -t btrfs $DEV0 -o degraded $MNT >& /dev/null
if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	rm $TMPIMG0 $TMPIMG1 $TMPIMG2
	echo "mount $DEV $MNT failed"
	exit 1
fi

#
# This used to fail, the fix resolves this failure
#
btrfs device add -f $DEV2 $MNT
rc=$?

umount $MNT

losetup -d $DEV0
losetup -d $DEV1
losetup -d $DEV2
rm $TMPIMG0 $TMPIMG1 $TMPIMG2
exit $rc
