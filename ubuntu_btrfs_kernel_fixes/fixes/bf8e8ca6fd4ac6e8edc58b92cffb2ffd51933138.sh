#!/bin/bash
cat << EOF
fix bf8e8ca6fd4ac6e8edc58b92cffb2ffd51933138

    Btrfs: send, don't delay dir move if there's a new parent inode

    If between two snapshots we rename an existing directory named X to Y and
    make it a child (direct or not) of a new inode named X, we were delaying
    the move/rename of the former directory unnecessarily, which would result
    in attempting to rename the new directory from its orphan name to name X
    prematurely.

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img
DEV0=/dev/loop0
DEV1=/dev/loop1
MNT0=$MNT/0
MNT1=$MNT/1

mkdir -p $MNT0 $MNT1

truncate --size 256M $TMPIMG0
truncate --size 256M $TMPIMG1

losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1

mkfs.btrfs -f "$DEV0" >& /dev/null
if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	rmdir -p $MNT0 $MNT1
	echo "mkfs.btrfs on $DEV0 failed"
	exit 1
fi
mount "$DEV0" "$MNT0"
if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	rmdir -p $MNT0 $MNT1
	echo "mount $DEV0 $MNT0 failed"
	exit 1
fi

mkfs.btrfs -f "$DEV1" >& /dev/null
if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	rmdir -p $MNT0 $MNT1
	echo "mkfs.btrfs on $DEV1 failed"
	exit 1
fi
mount "$DEV1" "$MNT1" -o compress=lzo
if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	rmdir -p $MNT0 $MNT1
	echo "mount $DEV1 $MNT1 failed"
	exit 1
fi

mkdir -p $MNT0/merlin/RC/OSD/Source
btrfs subvolume snapshot -r $MNT0 $MNT0/mysnap1

mkdir $MNT0/OSD
mv $MNT0/merlin/RC/OSD $MNT0/OSD/OSD-Plane_788
mv $MNT0/OSD $MNT0/merlin/RC

btrfs subvolume snapshot -r $MNT0 $MNT0/mysnap2

btrfs send $MNT0/mysnap1 -f /tmp/1.snap
btrfs send -p $MNT0/mysnap1 $MNT0/mysnap2 -f /tmp/2.snap

btrfs receive $MNT1 -f /tmp/1.snap
#
# Check for 3.16 regression, should NOT fail.
#  Failure message:
#     "rename o261-7-0 -> merlin/RC/OSD failed"
#
btrfs receive $MNT1 -f /tmp/2.snap
rc=$?

umount $DEV1
umount $DEV0

losetup -d $DEV1
losetup -d $DEV0

rm -f $TMPIMG0 $TMPIMG1
rm -rf $MNT0 $MNT1
exit $rc
