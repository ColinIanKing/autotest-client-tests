#!/bin/bash
cat << EOF
fix c55bfa67e94e22ec0449fe7c55b3ef20fbe13348

    Btrfs: set dead flag on the right root when destroying snapshot

    We were setting the BTRFS_ROOT_SUBVOL_DEAD flag on the root of the
    parent of our target snapshot, instead of setting it in the target
    snapshot's root.

    This is easy to observe by running the following scenario:

        mkfs.btrfs -f /dev/sdd
        mount /dev/sdd /mnt

        btrfs subvolume create /mnt/first_subvol
        btrfs subvolume snapshot -r /mnt /mnt/mysnap1

        btrfs subvolume delete /mnt/first_subvol
        btrfs subvolume snapshot -r /mnt /mnt/mysnap2

        btrfs send -p /mnt/mysnap1 /mnt/mysnap2 -f /tmp/send.data

    The send command failed because the send ioctl returned -EPERM.

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

btrfs subvolume create $MNT/first_subvol
if [ $? -ne 0 ]; then
	echo "btrfs subvolume create $MNT/first_subvol failed"
	umount $DEV
	losetup -d $DEV
	rm -f $TMPIMG
	exit 1
fi

btrfs subvolume snapshot -r $MNT $MNT/mysnap1
if [ $? -ne 0 ]; then
	echo "btrfs subvolume snapshot -r $MNT $MNT/mysnap1 failed"
	umount $DEV
	losetup -d $DEV
	rm -f $TMPIMG
	exit 1
fi

btrfs subvolume delete $MNT/first_subvol
if [ $? -ne 0 ]; then
	echo "btrfs subvolume delete $MNT/first_subvol failed"
	umount $DEV
	losetup -d $DEV
	rm -f $TMPIMG
	exit 1
fi

btrfs subvolume snapshot -r $MNT $MNT/mysnap2
if [ $? -ne 0 ]; then
	echo "btrfs subvolume snapshot -r $MNT $MNT/mysnap2 failed"
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
