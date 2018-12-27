#!/bin/bash
cat << EOF
fix bf0d1f441d1679136c25e6141dd7e66cc7a14218

    Btrfs: fix send issuing outdated paths for utimes, chown and chmod

    When doing an incremental send, if we had a directory pending a move/rename
    operation and none of its parents, except for the immediate parent, were
    pending a move/rename, after processing the directory's references, we would
    be issuing utimes, chown and chmod intructions against am outdated path - a
    path which matched the one in the parent root.

    This change also simplifies a bit the code that deals with building a path
    for a directory which has a move/rename operation delayed.

EOF

TMPIMG0=$TMP/test0.img
DEV0=/dev/loop0

truncate --size 1G $TMPIMG0
losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0 >& /dev/null
mount $DEV0 $MNT >& /dev/null

mkdir -p $MNT/a/b/c/d/e
mkdir $MNT/a/b/c/f
chmod 0777 $MNT/b/c/d/e
btrfs subvolume snapshot -r $MNT $MNT/snap1
btrfs send -f $TMP/base.send $MNT/snap1
mv $MNT/a/b/c/f $MNT/a/b/f2
mv $MNT/a/b/c/d/e $MNT/a/b/f2/e2
mv $MNT/a/b/c $MNT/a/b/c2
mv $MNT/a/b/c2/d $MNT/a/b/c2/d2
chmod 0700 $MNT/a/b/f2/e2
btrfs subvolume snapshot -r $MNT $MNT/snap2
btrfs send -p $MNT/snap1 -f $TMP/incremental.send $MNT/snap2

umount $MNT
mkfs.btrfs -f $DEV0
mount $DEV0 $MNT
btrfs receive -f $TMP/base.send $MNT
btrfs receive -f $TMP/incremental.send $MNT
rc=$?
if [ $rc -ne 0 ]; then
	echo "incremental receive failed with outdated paths for utimes, chown and chmod"
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
