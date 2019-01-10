#!/bin/bash
cat << EOF
fix 3821f348889e506efbd268cc8149e0ebfa47c4e5

    Btrfs: update commit root on snapshot creation after orphan cleanup

    On snapshot creation (either writable or read-only), we do orphan cleanup
    against the root of the snapshot. If the cleanup did remove any orphans,
    then the current root node will be different from the commit root node
    until the next transaction commit happens.

    A send operation always uses the commit root of a snapshot - this means
    it will see the orphans if it starts computing the send stream before the
    next transaction commit happens (triggered by a timer or sync() for .e.g),
    which is when the commit root gets assigned a reference to current root,
    where the orphans are not visible anymore. The consequence of send seeing
    the orphans is explained below.

    For example:

        mkfs.btrfs -f /dev/sdd
        mount -o commit=999 /dev/sdd /mnt

        # open a file with O_TMPFILE and leave it open
        # write some data to the file
        btrfs subvolume snapshot -r /mnt /mnt/snap1

        btrfs send /mnt/snap1 -f /tmp/send.data

    The send operation will fail with the following error:
        ERROR: send ioctl failed with -116: Stale file handle

EOF

gcc ${FIX}.c -o ${FIX}.out
if [ $? -ne 0 ]; then
	echo "Failed to build ${FIX}.c"
	exit 1
fi

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

${FIX}.out $MNT &
pid=$!
sleep 1

btrfs subvolume snapshot -r $MNT $MNT/snap1
if [ $? -ne 0 ]; then
	echo "btrfs subvolume snapshot -r $MNT $MNT/snap1 failed"
	kill -SIGUSR1 $pid
	wait $pid
	umount $DEV
	losetup -d $DEV
	rm -f $TMPIMG ${FIX}.out
	exit 1
fi
btrfs send -f /tmp/send.data $MNT/snap1
if [ $? -ne 0 ]; then
	echo "btrfs send $MNT/snap1 -f /tmp/send.data failed"
	kill -SIGUSR1 $pid
	wait $pid
	umount $DEV
	losetup -d $DEV
	rm -f $TMPIMG ${FIX}.out /tmp/send.data
	exit 1
fi

kill -SIGUSR1 $pid
wait $pid
umount $DEV
losetup -d $DEV
rm -f $TMPIMG ${FIX}.out /tmp/send.data
