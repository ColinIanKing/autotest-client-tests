#!/bin/bash
cat << EOF
fix c55f13964008bfea7c5bee268f28b699cbad7f00

Btrfs: fix deadlock when mounting a degraded fs

    The deadlock happened when we mount degraded filesystem, the reproduced
    steps are following:
     # mkfs.btrfs -f -m raid1 -d raid1 <dev0> <dev1>
     # echo 1 > /sys/block/`basename <dev0>`/device/delete
     # mount -o degraded <dev1> <mnt>

    The reason was that the counter -- bi_remaining was wrong. If the missing
    or unwriteable device was the last device in the mapping array, we would
    not submit the original bio, so we shouldn't increase bi_remaining of it
    in btrfs_end_bio(), or we would skip the final endio handle.

    Fix this problem by adding a flag into btrfs bio structure. If we submit
    the original bio, we will set the flag, and we increase bi_remaining counter,
    or we don't.

    Though there is another way to fix it -- decrease bi_remaining counter of the
    original bio when we make sure the original bio is not submitted, this method
    need add more check and is easy to make mistake.

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img

DEV0=/dev/loop0
DEV1=/dev/loop1

truncate --size 2G $TMPIMG0
truncate --size 2G $TMPIMG1

losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1

mkfs.btrfs -f -m raid1 $DEV0 $DEV1 >& /dev/null
if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	echo "mkfs.btrfs -f $DEV0 $MNT failed"
	exit 1
fi

losetup -d $DEV0

mount -o degraded $DEV1 $MNT
if [ $? -eq 1 ]; then
	umount $MNT
	losetup -d $DEV1
	echo "mount $DEV0 on degraded raid1 failed"
	exit 1
fi

umount $MNT
losetup -d $DEV1
rm -f $TMPIMG0 $TMPIMG1
exit 0
