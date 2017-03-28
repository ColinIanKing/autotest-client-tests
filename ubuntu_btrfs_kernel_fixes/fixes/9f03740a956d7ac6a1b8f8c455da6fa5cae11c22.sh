#!/bin/bash
cat << EOF
fix 9f03740a956d7ac6a1b8f8c455da6fa5cae11c22

    Btrfs: fix infinite path build loops in incremental send

    The send operation processes inodes by their ascending number, and assumes
    that any rename/move operation can be successfully performed (sent to the
    caller) once all previous inodes (those with a smaller inode number than the
    one we're currently processing) were processed.

    [ .... ]

    Even without this loop, the incremental send couldn't succeed, because it would attempt
    to send a rename/move operation for the lower inode before the highest inode number was
    renamed/move. This issue is easy to trigger with the following steps:

      $ mkfs.btrfs -f /dev/sdb3
      $ mount /dev/sdb3 /mnt/btrfs
      $ mkdir -p /mnt/btrfs/a/b/c/d
      $ mkdir /mnt/btrfs/a/b/c2
      $ btrfs subvol snapshot -r /mnt/btrfs /mnt/btrfs/snap1
      $ mv /mnt/btrfs/a/b/c/d /mnt/btrfs/a/b/c2/d2
      $ mv /mnt/btrfs/a/b/c /mnt/btrfs/a/b/c2/d2/cc
      $ btrfs subvol snapshot -r /mnt/btrfs /mnt/btrfs/snap2
      $ btrfs send -p /mnt/btrfs/snap1 /mnt/btrfs/snap2 > /tmp/incremental.send

EOF

TMPIMG=$TMP/test.img
DEV=/dev/loop0

truncate --size 512M $TMPIMG

losetup $DEV $TMPIMG

mkfs.btrfs -f $DEV  >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV  >& /dev/null failed"
	losetup -d $DEV
	rm -f $TMPIMG
	exit 1
fi

mkdir $MNT/btrfs
mount $DEV $MNT/btrfs
if [ $? -ne 0 ]; then
	echo "mount $DEV $MNT failed"
	losetup -d $DEV
	rm -f $TMPIMG
	exit 1
fi

mkdir -p $MNT/btrfs/a/b/c/d
mkdir $MNT/btrfs/a/b/c2
btrfs subvol snapshot -r $MNT/btrfs $MNT/btrfs/snap1
mv $MNT/btrfs/a/b/c/d $MNT/btrfs/a/b/c2/d2
mv $MNT/btrfs/a/b/c $MNT/btrfs/a/b/c2/d2/cc
btrfs subvol snapshot -r $MNT/btrfs $MNT/btrfs/snap2
btrfs send -p $MNT/btrfs/snap1 $MNT/btrfs/snap2 > /tmp/incremental.send

umount $MNT/btrfs
losetup -d $DEV
rm -f $TMPIMG /tmp/incremental.send
exit $rc
