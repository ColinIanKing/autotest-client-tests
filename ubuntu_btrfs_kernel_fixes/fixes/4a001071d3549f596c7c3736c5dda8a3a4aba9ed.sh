#!/bin/bash
cat << EOF
fix 4a001071d3549f596c7c3736c5dda8a3a4aba9ed

    Btrfs: fix loop device on top of btrfs

    We cannot use the loop device which has been connected to a file in the btrf

    The reproduce steps is following:
     # dd if=/dev/zero of=vdev0 bs=1M count=1024
     # losetup /dev/loop0 vdev0
     # mkfs.btrfs /dev/loop0
     ...
     failed to zero device start -5

    The reason is that the btrfs don't implement either ->write_begin or ->write
    the VFS API, so we fix it by setting ->write to do_sync_write().

EOF

TMPIMG0=$TMP/test0.img

DEV0=`losetup -f`

dd if=/dev/zero of=$TMPIMG0 bs=1M count=1024 >& /dev/null

losetup $DEV0 $TMPIMG0

mkfs.btrfs $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 $DEV1 failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

mount $DEV0 $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
modprobe btrfs
exit 0
