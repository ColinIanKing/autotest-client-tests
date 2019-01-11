#!/bin/bash
cat << EOF
fix 2b863a135f22f242ba4fc669f3a6b2f6c826832c

   Btrfs: incremental send, fix invalid path after dir rename

    This fixes yet one more case not caught by the commit titled:

       Btrfs: fix infinite path build loops in incremental send

    In this case, even before the initial full send, we have a directory
    which is a child of a directory with a higher inode number. Then we
    perform the initial send, and after we rename both the child and the
    parent, without moving them around. After doing these 2 renames, an
    incremental send sent a rename instruction for the child directory
    which contained an invalid "from" path (referenced the parent's old
    name, not the new one), which made the btrfs receive command fail.

EOF

TMPIMG0=$TMP/test0.img
DEV0=`losetup -f`

truncate --size 1G $TMPIMG0
losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0
mount $DEV0 $MNT
mkdir -p $MNT/a/b
mkdir $MNT/d
mkdir $MNT/a/b/c
mv $MNT/d $MNT/a/b/c
btrfs subvolume snapshot -r $MNT $MNT/snap1
btrfs send -f $TMP/base.send $MNT/snap1
mv $MNT/a/b/c $MNT/a/b/x
mv $MNT/a/b/x/d $MNT/a/b/x/y
btrfs subvolume snapshot -r $MNT $MNT/snap2
btrfs send -p $MNT/snap1 -f $TMP/incremental.send $MNT/snap2

umount $MNT
mkfs.btrfs -f $DEV0
mount $DEV0 $MNT
btrfs receive -f $TMP/base.send $MNT
btrfs receive -f $TMP/incremental.send $MNT

rc=$?
if [ $rc -ne 0 ]; then
	echo "incremental receive failed"
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
