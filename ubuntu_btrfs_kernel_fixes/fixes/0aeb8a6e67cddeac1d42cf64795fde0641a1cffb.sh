#!/bin/bash
cat << EOF
fix 0aeb8a6e67cddeac1d42cf64795fde0641a1cffb

    btrfs: fix null pointer dereference in btrfs_show_devname when name is null

    dev->name is null but missing flag is not set.
    Strictly speaking the missing flag should have been set, but there
    are more places where code just checks if name is null. For now this
    patch does the same.

    stack:
    BUG: unable to handle kernel NULL pointer dereference at 0000000000000064
    IP: [<ffffffffa0228908>] btrfs_show_devname+0x58/0xf0 [btrfs]

    [<ffffffff81198879>] show_vfsmnt+0x39/0x130
    [<ffffffff81178056>] m_show+0x16/0x20
    [<ffffffff8117d706>] seq_read+0x296/0x390
    [<ffffffff8115aa7d>] vfs_read+0x9d/0x160
    [<ffffffff8115b549>] SyS_read+0x49/0x90
    [<ffffffff817abe52>] system_call_fastpath+0x16/0x1b

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img
TMPIMG2=$TMP/test2.img

DEV0=/dev/loop0
DEV1=/dev/loop1
DEV2=/dev/loop2

truncate --size 2G $TMPIMG0
truncate --size 2G $TMPIMG1
truncate --size 2G $TMPIMG2

losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1
losetup $DEV2 $TMPIMG2

dmesg -c > /dev/null

mkfs.btrfs -f -draid1 $DEV0 $DEV1 >& /dev/null
if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
	echo "mkfs.btrfs -f $DEV0 $DEV1 failed"
	exit 1
fi

btrfstune -S 1 $DEV0
modprobe -r btrfs && modprobe btrfs

mount -o degraded $DEV0 $MNT
if [ $? -ne 0 ]; then
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
	echo "mount $DEV $MNT failed"
	exit 1
fi

btrfs dev add $DEV2 $MNT
rc=0
n=$(dmesg | grep "BUG" | wc -l)
if [ $n -gt 0 ]; then
	echo "mount failed, kernel bug:"
	dmesg
	umount $MNT
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
	rc=1
fi

umount $MNT
losetup -d $DEV0
losetup -d $DEV1
losetup -d $DEV2
rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
exit $rc
