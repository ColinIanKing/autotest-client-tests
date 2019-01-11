#!/bin/bash
cat << EOF
fix 29d6d30f5c8aa58b04f40a58442df3bcaae5a1d5

    Btrfs: send, don't send rmdir for same target multiple times

    When doing an incremental send, if we delete a directory that has N > 1
    hardlinks for the same file and that file has the highest inode number
    inside the directory contents, an incremental send would send N times an
    rmdir operation against the directory. This made the btrfs receive command
    fail on the second rmdir instruction, as the target directory didn't exist
    anymore.

EOF

TMPIMG0=$TMP/test0.img
DEV0=`losetup -f`

truncate --size 1G $TMPIMG0
losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0
mount $DEV0 $MNT
mkdir -p $MNT/a/b/c
echo 'ola mundo' > $MNT/a/b/c/foo.txt
ln $MNT/a/b/c/foo.txt $MNT/a/b/c/bar.txt
btrfs subvolume snapshot -r $MNT $MNT/snap1
btrfs send -f $TMP/base.send $MNT/snap1
rm -f $MNT/a/b/c/foo.txt
rm -f $MNT/a/b/c/bar.txt
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
	echo "incremental receive failed"
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
