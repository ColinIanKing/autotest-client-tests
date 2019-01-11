#!/bin/bash -x
cat << EOF
fix 84471e2429ed82fdbac0c56d5b2a18d450f99f6a

    Btrfs: incremental send, don't rename a directory too soon

    There's one more case where we can't issue a rename operation for a
    directory as soon as we process it. We used to delay directory renames
    only if they have some ancestor directory with a higher inode number
    that got renamed too, but there's another case where we need to delay
    the rename too - when a directory A is renamed to the old name of a
    directory B but that directory B has its rename delayed because it
    has now (in the send root) an ancestor with a higher inode number that
    was renamed. If we don't delay the directory rename in this case, the
    receiving end of the send stream will attempt to rename A to the old
    name of B before B got renamed to its new name, which results in a
    "directory not empty" error. So fix this by delaying directory renames
    for this case too.

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img

MNT0=$MNT/0
MNT1=$MNT/1

rm -rf $MNT0 $MNT1
mkdir $MNT0 $MNT1

truncate --size 1G $TMPIMG0
truncate --size 1G $TMPIMG1

DEV0=`losetup -f`
losetup $DEV0 $TMPIMG0

DEV1=`losetup -f`
losetup $DEV1 $TMPIMG1

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	echo "mkfs.btrfs -f $DEV0 failed"
	exit 1
fi

mkfs.btrfs -f $DEV1 >& /dev/null
if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	echo "mkfs.btrfs -f $DEV0 failed"
	exit 1
fi

mount $DEV0 $MNT0
mount $DEV1 $MNT1

mkdir $MNT0/a
mkdir $MNT0/b
mkdir $MNT0/c
mkdir $MNT0/a/file

btrfs subvolume snapshot -r $MNT0 $MNT0/snap1

mv $MNT0/c $MNT0/x
mv $MNT0/a $MNT0/x/y
mv $MNT0/b $MNT0/q

btrfs subvolume snapshot -r $MNT0 $MNT0/snap2

btrfs send -f /tmp/1.send $MNT0/snap1
btrfs send -p $MNT0/snap1 -f /tmp/2.send $MNT0/snap2

btrfs receive -f /tmp/1.send $MNT1
btrfs receive -f /tmp/2.send $MNT1
rc=$?
if [ $rc -ne 0 ]; then
	echo "failed: btrfs receive $MN1 -f /tmp/2.send failed"
fi

umount $MNT0

losetup -d $DEV0
losetup -d $DEV1
rm -f $TMPIMG0 $TMPIMG1
exit $rc
