#!/bin/bash
cat << EOF
fix c7c144db531fda414e532adac56e965ce332e2a5

    Btrfs: update global block_rsv when creating a new block group

    A bug was triggered while using seed device:

        # mkfs.btrfs /dev/loop1
        # btrfstune -S 1 /dev/loop1
        # mount -o /dev/loop1 /mnt
        # btrfs dev add /dev/loop2 /mnt

    btrfs: block rsv returned -28
    ------------[ cut here ]------------
    WARNING: at fs/btrfs/extent-tree.c:5969 btrfs_alloc_free_block+0x166/0x396 [btrfs]()

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img
DEV0=/dev/loop0
DEV1=/dev/loop1

truncate --size 256M $TMPIMG0
truncate --size 256M $TMPIMG1
losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs $DEV0 failed"
	losetup -d $DEV0
	rm $TMPIMG0
	exit 1
fi

btrfstune -S 1 $DEV0

mount $DEV0 $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT failed"
	losetup -d $DEV0 $DEV1
	rm $TMPIMG0 $TMPIMG1
	exit 1
fi

#
# The following will force a crash / hang
# that never exits if the bug was not fixed
#
btrfs dev add $DEV1 $MNT

rc=0

umount $MNT >& /dev/null
losetup -d $DEV0
losetup -d $DEV1
rm $TMPIMG0 $TMPIMG0
exit $rc
