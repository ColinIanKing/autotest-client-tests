#!/bin/bash
cat << EOF
fix c992ec94f24c3e7135d6c23860615f269f0b1d87

    Btrfs: send, account for orphan directories when building path strings

    If we have directories with a pending move/rename operation, we must take into
    account any orphan directories that got created before executing the pending
    move/rename. Those orphan directories are directories with an inode number higher
    then the current send progress and that don't exist in the parent snapshot, they
    are created before current progress reaches their inode number, with a generated
    name of the form oN-M-I and at the root of the filesystem tree, and later when
    progress matches their inode number, moved/renamed to their final location.

    Reproducer:

              $ mkfs.btrfs -f /dev/sdd
              $ mount /dev/sdd /mnt

              $ mkdir -p /mnt/a/b/c/d
              $ mkdir /mnt/a/b/e
              $ mv /mnt/a/b/c /mnt/a/b/e/CC
              $ mkdir /mnt/a/b/e/CC/d/f
          $ mkdir /mnt/a/g

              $ btrfs subvolume snapshot -r /mnt /mnt/snap1
              $ btrfs send /mnt/snap1 -f /tmp/base.send

              $ mkdir /mnt/a/g/h
          $ mv /mnt/a/b/e /mnt/a/g/h/EE
              $ mv /mnt/a/g/h/EE/CC/d /mnt/a/g/h/EE/DD

              $ btrfs subvolume snapshot -r /mnt /mnt/snap2
              $ btrfs send -p /mnt/snap1 /mnt/snap2 -f /tmp/incremental.send

    The second receive command failed with the following error:

        ERROR: rename a/b/e/CC/d -> o264-7-0/EE/DD failed. No such file or directory

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

mkdir -p $MNT/a/b/c/d
mkdir $MNT/a/b/e
mv $MNT/a/b/c $MNT/a/b/e/CC
mkdir $MNT/a/b/e/CC/d/f
mkdir $MNT/a/g

btrfs subvolume snapshot -r $MNT $MNT/mysnap1
if [ $? -ne 0 ]; then
	echo "btrfs subvolume snapshot -r $MNT $MNT/mysnap1 failed"
	umount $DEV
	losetup -d $DEV
	rm -f $TMPIMG
	exit 1
fi
btrfs send -f /tmp/base.send $MNT/mysnap1
if [ $? -ne 0 ]; then
	echo "btrfs send -f /tmp/base.send $MNT/mysnap1 failed"
	umount $DEV
	losetup -d $DEV
	rm -f $TMPIMG /tmp/base.send
	exit 1
fi

mkdir $MNT/a/g/h
mv $MNT/a/b/e $MNT/a/g/h/EE
mv $MNT/a/g/h/EE/CC/d $MNT/a/g/h/EE/DD

btrfs subvolume snapshot -r $MNT $MNT/mysnap2
if [ $? -ne 0 ]; then
	echo "btrfs subvolume snapshot -r $MNT $MNT/mysnap2 failed"
	umount $DEV
	losetup -d $DEV
	rm -f $TMPIMG /tmp/base.send
	exit 1
fi
btrfs send -p $MNT/mysnap1 -f /tmp/incremental.send $MNT/mysnap2
if [ $? -ne 0 ]; then
	echo "btrfs send -p $MNT/mysnap1 -f /tmp/incremental.send $MNT/mysnap2 failed"
	umount $DEV
	losetup -d $DEV
	rm -f $TMPIMG /tmp/base.send /tmp/incremental.send
	exit 1
fi


umount $DEV
losetup -d $DEV
rm -f $TMPIMG /tmp/base.send /tmp/incremental.send
exit 0
