#!/bin/bash
cat << EOF
fix bfa7e1f8be4bd7118e485a42cc8889530d415d05

    Btrfs: part 2, fix incremental send's decision to delay a dir move/rename

    For an incremental send, fix the process of determining whether the directory
    inode we're currently processing needs to have its move/rename operation delayed.

    We were ignoring the fact that if the inode's new immediate ancestor has a higher
    inode number than ours but wasn't renamed/moved, we might still need to delay our
    move/rename, because some other ancestor directory higher in the hierarchy might
    have an inode number higher than ours *and* was renamed/moved too - in this case
    we have to wait for rename/move of that ancestor to happen before our current
    directory's rename/move operation.

EOF

TMPIMG0=$TMP/test0.img
DEV0=/dev/loop0

truncate --size 1G $TMPIMG0
losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0
mount $DEV0 $MNT

mkdir -p $MNT/a/x1/x2
mkdir $MNT/a/Z
mkdir -p $MNT/a/x1/x2/x3/x4/x5

btrfs subvolume snapshot -r $MNT $MNT/snap1
btrfs send -f $TMP/base.send $MNT/snap1

mv $MNT/a/x1/x2/x3 $MNT/a/Z/X33
mv $MNT/a/x1/x2 $MNT/a/Z/X33/x4/x5/X22

btrfs subvolume snapshot -r $MNT $MNT/snap2
btrfs send -p $MNT/snap1 -f $TMP/incremental.send $MNT/snap2

rc=$?
if [ $rc -ne 0 ]; then
	echo "incremental receive failed"
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
