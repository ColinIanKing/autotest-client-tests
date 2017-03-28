#!/bin/bash
cat << EOF
fix 5ed7f9ff15e6ea56bcb78f69e9503dc1a587caf0

    Btrfs: more send support for parent/child dir relationship inversion

    The commit titled "Btrfs: fix infinite path build loops in incremental send"
    didn't cover a particular case where the parent-child relationship inversion
    of directories doesn't imply a rename of the new parent directory. This was
    due to a simple logic mistake, a logical and instead of a logical or.

EOF

TMPIMG0=$TMP/test0.img
DEV0=/dev/loop0

truncate --size 1G $TMPIMG0
losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0
mount $DEV0 $MNT

umount $MNT
mkfs.btrfs -f $DEV0
mount $DEV0 $MNT

mkdir -p $MNT/a/b/bar1/bar2/bar3/bar4
btrfs subvol snapshot -r $MNT $MNT/snap1
mv $MNT/a/b/bar1/bar2/bar3/bar4 $MNT/a/b/k44
mv $MNT/a/b/bar1/bar2/bar3 $MNT/a/b/k44
mv $MNT/a/b/bar1/bar2 $MNT/a/b/k44/bar3
mv $MNT/a/b/bar1 $MNT/a/b/k44/bar3/bar2/k11
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
