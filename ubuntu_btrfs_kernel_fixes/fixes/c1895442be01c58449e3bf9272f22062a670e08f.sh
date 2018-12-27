#!/bin/bash
cat << EOF
fix c1895442be01c58449e3bf9272f22062a670e08f.

    Btrfs: send, don't error in the presence of subvols/snapshots

    If we are doing an incremental send and the base snapshot has a
    directory with name X that doesn't exist anymore in the second
    snapshot and a new subvolume/snapshot exists in the second snapshot
    that has the same name as the directory (name X), the incremental
    send would fail with -ENOENT error. This is because it attempts
    to lookup for an inode with a number matching the objectid of a
    root, which doesn't exist.

    Steps to reproduce:

        mkfs.btrfs -f /dev/sdd
        mount /dev/sdd /mnt

        mkdir /mnt/testdir
        btrfs subvolume snapshot -r /mnt /mnt/mysnap1

        rmdir /mnt/testdir
        btrfs subvolume create /mnt/testdir
        btrfs subvolume snapshot -r /mnt /mnt/mysnap2

        btrfs send -p /mnt/mysnap1 /mnt/mysnap2 -f /tmp/send.data

EOF

TMPIMG=$TMP/test.img
DEV=/dev/loop0

truncate --size 256M $TMPIMG
losetup $DEV $TMPIMG

mkfs.btrfs -f "$DEV" >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs on $DEV failed"
	losetup -d $DEV
	rm -f $TMPIMG
	exit 1
fi
mount "$DEV" "$MNT" -o commit=999
if [ $? -ne 0 ]; then
	echo "mount $DEV $MNT failed"
	losetup -d $DEV
	rm -f $TMPIMG
	exit 1
fi

mkdir $MNT/testdir
btrfs subvolume snapshot -r $MNT $MNT/mysnap1
if [ $? -ne 0 ]; then
	echo "btrfs subvolume snapshot -r $MNT $MNT/mysnap1 failed"
	umount $DEV
	losetup -d $DEV
	rm -f $TMPIMG
	exit 1
fi

rmdir $MNT/testdir
btrfs subvolume create  $MNT/testdir
if [ $? -ne 0 ]; then
	echo "btrfs subvolume delete $MNT/first_subvol failed"
	umount $DEV
	losetup -d $DEV
	rm -f $TMPIMG
	exit 1
fi
btrfs subvolume snapshot -r $MNT $MNT/mysnap2
if [ $? -ne 0 ]; then
	echo "btrfs subvolume snapshot -r $MNT $MNT/mysnap1 failed"
	umount $DEV
	losetup -d $DEV
	rm -f $TMPIMG
	exit 1
fi
btrfs send -p $MNT/mysnap1 -f /tmp/send.data $MNT/mysnap2
if [ $? -ne 0 ]; then
	echo "btrfs send -p $MNT/mysnap1 -f /tmp/send.data $MNT/mysnap2 failed"
	umount $DEV
	losetup -d $DEV
	rm -f $TMPIMG /tmp/send.data
	exit 1
fi

umount $DEV
losetup -d $DEV
rm -f $TMPIMG /tmp/send.data
exit 0
