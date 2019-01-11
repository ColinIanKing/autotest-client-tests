#!/bin/bash
cat << EOF
fix 9dc442143b9874ba677fc83bf8c60744ec642998

    Btrfs: fix send attempting to rmdir non-empty directories

    The incremental send algorithm assumed that it was possible to issue
    a directory remove (rmdir) if the the inode number it was currently
    processing was greater than (or equal) to any inode that referenced
    the directory's inode. This wasn't a valid assumption because any such
    inode might be a child directory that is pending a move/rename operation,
    because it was moved into a directory that has a higher inode number and
    was moved/renamed too - in other words, the case the following commit
    addressed:

        9f03740a956d7ac6a1b8f8c455da6fa5cae11c22
        (Btrfs: fix infinite path build loops in incremental send)

    This made an incremental send issue an rmdir operation before the
    target directory was actually empty, which made btrfs receive fail.
    Therefore it needs to wait for all pending child directory inodes to

EOF

TMPIMG0=$TMP/test0.img
DEV0=`losetup -f`

truncate --size 1G $TMPIMG0
losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0 >& /dev/null
mount $DEV0 $MNT >& /dev/null

mkdir -p $MNT/a/b/c/x
mkdir $MNT/a/b/y
btrfs subvolume snapshot -r $MNT $MNT/snap1
btrfs send -f $TMP/base.send $MNT/snap1
mv $MNT/a/b/y $MNT/a/b/YY
mv $MNT/a/b/c/x $MNT/a/b/YY
rmdir $MNT/a/b/c
btrfs subvolume snapshot -r $MNT $MNT/snap2
btrfs send -p $MNT/snap1 -f $TMP/incremental.send $MNT/snap2

umount $MNT
mkfs.btrfs -f $DEV0
mount $DEV0 $MNT

btrfs receive -f $TMP/base.send $MNT
btrfs receive -f $TMP/incremental.send $MNT

rc=$?
if [ $rc -ne 0 ]; then
	echo "incremental receive failed with rmdir on non-empty directories"
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
