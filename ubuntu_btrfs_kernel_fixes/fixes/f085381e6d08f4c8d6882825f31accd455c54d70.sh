#!/bin/bash
cat << EOF
fix f085381e6d08f4c8d6882825f31accd455c54d70

    btrfs: fix null pointer deference at btrfs_sysfs_add_one+0x105

    bdev is null when disk has disappeared and mounted with
    the degrade option

    stack trace
    ---------
    btrfs_sysfs_add_one+0x105/0x1c0 [btrfs]
    open_ctree+0x15f3/0x1fe0 [btrfs]
    btrfs_mount+0x5db/0x790 [btrfs]
    ? alloc_pages_current+0xa4/0x160
    mount_fs+0x34/0x1b0
    vfs_kern_mount+0x62/0xf0
    do_mount+0x22e/0xa80
    ? __get_free_pages+0x9/0x40
    ? copy_mount_options+0x31/0x170
    SyS_mount+0x7e/0xc0
    system_call_fastpath+0x16/0x1b
    ---------

    reproducer:
    -------
    mkfs.btrfs -draid1 -mraid1 /dev/sdc /dev/sdd
    (detach a disk)
    devmgt detach /dev/sdc [1]
    mount -o degrade /dev/sdd /btrfs
    -------

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img

truncate --size 512M $TMPIMG0
truncate --size 512M $TMPIMG1

DEV0=`losetup -f`
losetup $DEV0 $TMPIMG0

DEV1=`losetup -f`
losetup $DEV1 $TMPIMG1

mkfs.btrfs -f -draid1 -mraid1 $DEV0 $DEV1 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f -draid1 -mraid1 $DEV0 $DEV1 failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

losetup -d $DEV0

dmesg -c > /dev/null
#
# This will fail, so ignore errors
#
mount -o degrade $DEV1 $MNT >& /dev/null

#
# Anything blow up?
#
dumped=$(dmesg | grep "btrfs_sysfs_add_one" | wc -l)
if [ $dumped -gt 0 ]; then
	echo "found a kernel stack dump"
	dmesg
	losetup -d $DEV0 $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	exit 1
fi

umount $MNT >& /dev/null
losetup -d $DEV1
rm -f $TMPIMG0 $TMPIMG1
