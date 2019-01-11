#!/bin/bash
cat << EOF
fix 03cb4fb9d86d591bc8a3f66eac6fb874b50b1b4d

    Btrfs: fix send dealing with file renames and directory moves

    This fixes a case that the commit titled:

       Btrfs: fix infinite path build loops in incremental send

    didn't cover. If the parent-child relationship between 2 directories
    is inverted, both get renamed, and the former parent has a file that
    got renamed too (but remains a child of that directory), the incremental
    send operation would use the file's old path after sending an unlink
    operation for that old path, causing receive to fail on future operations
    like changing owner, permissions or utimes of the corresponding inode.

    This is not a regression from the commit mentioned before, as without
    that commit we would fall into the issues that commit fixed, so it's
    just one case that wasn't covered before.

EOF

TMPIMG0=$TMP/test0.img
DEV0=`losetup -f`

truncate --size 1G $TMPIMG0
losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0
mount $DEV0 $MNT

mkdir -p $MNT/a/b/c/d
touch $MNT/a/b/c/d/file
mkdir -p $MNT/a/b/x
btrfs subvol snapshot -r $MNT $MNT/snap1
mv $MNT/a/b/x $MNT/a/b/c/x2
mv $MNT/a/b/c/d $MNT/a/b/c/x2/d2
mv $MNT/a/b/c/x2/d2/file $MNT/a/b/c/x2/d2/file2
btrfs subvol snapshot -r $MNT $MNT/snap2
btrfs send -p $MNT/snap1 $MNT/snap2 > $TMP/incremental.send

rc=$?
if [ $rc -ne 0 ]; then
	echo "incremental send failed"
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
