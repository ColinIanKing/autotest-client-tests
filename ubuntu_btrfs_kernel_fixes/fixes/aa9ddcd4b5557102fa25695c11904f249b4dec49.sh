#!/bin/bash
cat << EOF
fix aa9ddcd4b5557102fa25695c11904f249b4dec49

    Btrfs: do not use missing devices when showing devname

    If you do the following

    mkfs.btrfs /dev/sdb /dev/sdc
    rmmod btrfs
    dd if=/dev/zero of=/dev/sdb bs=1M count=1
    mount -o degraded /dev/sdc /mnt/btrfs-test

    the box will panic trying to deref the name for the missing dev since it is
    the lower numbered devid.  So fix show_devname to not use missing devices.

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img

DEV0=/dev/loop0
DEV1=/dev/loop1

truncate --size 512M $TMPIMG0
truncate --size 512M $TMPIMG1

losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1

mkfs.btrfs -f $DEV0 $DEV1 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 $DEV1 failed"
	losetup -d $DEV0 $DEV1
	rm $TMPIMG0 $TMPIMG1
	exit 1
fi

rmmod btrfs

dd if=/dev/zero of=$DEV0 bs=1M count=1 >& /dev/null

#
# The following will panic unfixed kernels
#
mount -o degraded $DEV1 $MNT >& /dev/null

umount $MNT >& /dev/null
losetup -d $DEV0 $DEV1
rm $TMPIMG0 $TMPIMG1
modprobe btrfs
exit 0
