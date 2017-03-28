#!/bin/bash
cat << EOF
fix d7ce5843bb28ada6845ab2ae8510ba3f12d33154

    Btrfs: remove BUG_ON() due to mounting bad filesystem

    Mounting a bad filesystem caused a BUG_ON(). The following is steps to
    reproduce it.
     # mkfs.btrfs /dev/sda2
     # mount /dev/sda2 /mnt
     # mkfs.btrfs /dev/sda1 /dev/sda2
     (the program says that /dev/sda2 was mounted, and then exits. )
     # umount /mnt
     # mount /dev/sda1 /mnt

    At the third step, mkfs.btrfs exited in the way of make filesystem. So the
    initialization of the filesystem didn't finish. So the filesystem was bad, and
    it caused BUG_ON() when mounting it. But BUG_ON() should be called by the wrong
    code, not user's operation, so I think it is a bug of btrfs.

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img

DEV0=/dev/loop0
DEV1=/dev/loop1

truncate --size 512M $TMPIMG0
truncate --size 512M $TMPIMG1

losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1

mkfs.btrfs -f $DEV1 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV1 failed"
	losetup -d $DEV0 $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	exit 1
fi

mount $DEV1 $MNT

#
# We expect this to fail rather than to BUG_ON
#
mkfs.btrfs -f $DEV0 $DEV1 >& /dev/null
if [ $? -eq 0 ]; then
	echo "mkfs.btrfs -f $DEV0 $DEV1 did not fail as expected"
	umount $MNT >& /dev/null
	losetup -d $DEV0 $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	exit 1
fi

umount $MNT >& /dev/null
losetup -d $DEV0 $DEV1
rm -f $TMPIMG0 $TMPIMG1
modprobe btrfs
exit 0
