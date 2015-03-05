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
DEV0=/dev/loop0

truncate --size 1G $TMPIMG0
losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0
mount $DEV0 $MNT
mkdir -p $MNT/a/b
mkdir $MNT/d
mkdir $MNT/a/b/c
mv $MNT/d $MNT/a/b/c
btrfs subvolume snapshot -r $MNT $MNT/snap1
btrfs send $MNT/snap1 -f $TMP/base.send
mv $MNT/a/b/c $MNT/a/b/x
mv $MNT/a/b/x/d $MNT/a/b/x/y
btrfs subvolume snapshot -r $MNT $MNT/snap2
btrfs send -p $MNT/snap1 $MNT/snap2 -f $TMP/incremental.send

umount $MNT
mkfs.btrfs -f $DEV0
mount $DEV0 $MNT
btrfs receive $MNT -f $TMP/base.send
btrfs receive $MNT -f $TMP/incremental.send

rc=$?
if [ $rc -ne 0 ]; then
	echo "incremental receive failed"
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm $TMPIMG0
exit $rc
