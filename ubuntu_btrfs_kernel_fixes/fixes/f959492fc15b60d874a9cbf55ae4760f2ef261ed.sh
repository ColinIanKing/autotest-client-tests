#!/bin/bash
cat << EOF
fix f959492fc15b60d874a9cbf55ae4760f2ef261ed

    Btrfs: send, fix more issues related to directory renames

    This is a continuation of the previous changes titled:

       Btrfs: fix incremental send's decision to delay a dir move/rename
       Btrfs: part 2, fix incremental send's decision to delay a dir move/rename

    There's a few more cases where a directory rename/move must be delayed which was
    previously overlooked. If our immediate ancestor has a lower inode number than
    ours and it doesn't have a delayed rename/move operation associated to it, it
    doesn't mean there isn't any non-direct ancestor of our current inode that needs
    to be renamed/moved before our current inode (i.e. with a higher inode number
    than ours).

    So we can't stop the search if our immediate ancestor has a lower inode number than
    ours, we need to navigate the directory hierarchy upwards until we hit the root or:

    1) find an ancestor with an higher inode number that was renamed/moved in the send
       root too (or already has a pending rename/move registered);
    2) find an ancestor that is a new direc

EOF

TMPIMG0=$TMP/test0.img
DEV0=/dev/loop0

truncate --size 1G $TMPIMG0
losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0
mount $DEV0 $MNT

mkdir -p $MNT/a/b
mkdir -p $MNT/a/c/d
mkdir $MNT/a/b/e
mkdir $MNT/a/c/d/f
mv $MNT/a/b $MNT/a/c/d/2b
mkdir $MNT/a/x
mkdir $MNT/a/y

btrfs subvolume snapshot -r $MNT $MNT/snap1
btrfs send $MNT/snap1 -f $TMP/base.send

mv $MNT/a/x $MNT/a/y
mv $MNT/a/c/d/2b/e $MNT/a/c/d/2b/2e
mkdir $MNT/a/h
mv $MNT/a/c/d $MNT/a/h/2d
mv $MNT/a/c $MNT/a/h/2d/2b/2c

btrfs subvolume snapshot -r $MNT $MNT/snap2
btrfs send -p $MNT/snap1 $MNT/snap2 -f $TMP/incremental.send
rc=$?
if [ $rc -ne 0 ]; then
	echo "incremental receive failed"
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
