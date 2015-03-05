#!/bin/bash
cat << EOF
fix 115930cb2d444a684975cf2325759cb48ebf80cc

    Btrfs: fix wrong write offset when replacing a device

    Miao Xie reported the following issue:

    The filesystem was corrupted after we did a device replace.

    Steps to reproduce:
     # mkfs.btrfs -f -m single -d raid10 <device0>..<device3>
     # mount <device0> <mnt>
     # btrfs replace start -rfB 1 <device4> <mnt>
     # umount <mnt>
     # btrfsck <device4>

    The reason for the issue is that we changed the write offset by mistake,
    introduced by commit 625f1c8dc.

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img
TMPIMG2=$TMP/test2.img
TMPIMG3=$TMP/test3.img
TMPIMG4=$TMP/test4.img

DEV0=/dev/loop0
DEV1=/dev/loop1
DEV2=/dev/loop2
DEV3=/dev/loop3
DEV4=/dev/loop4

truncate --size 1G $TMPIMG0
truncate --size 1G $TMPIMG1
truncate --size 1G $TMPIMG2
truncate --size 1G $TMPIMG3
truncate --size 1G $TMPIMG4

losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1
losetup $DEV2 $TMPIMG2
losetup $DEV3 $TMPIMG3
losetup $DEV4 $TMPIMG4

mkfs.btrfs -f -m single -d raid10 $DEV0 $DEV1 $DEV2 $DEV3 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f -m single -d raid10 $DEV0 $DEV1 $DEV2 $DEV3 failed"
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	losetup -d $DEV3
	losetup -d $DEV4
	rm $TMPIMG0 $TMPIMG1 $TMPIMG2 $TMPIMG3 $TMPIMG4
	exit 1
fi

mount $DEV0 $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT failed"
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	losetup -d $DEV3
	losetup -d $DEV4
	rm $TMPIMG0 $TMPIMG1 $TMPIMG2 $TMPIMG3 $TMPIMG4
	exit 1
fi

btrfs replace start -rfB 1 $DEV4 $MNT
umount $MNT >& /dev/null

btrfsck $DEV4
if [ $? -ne 0 ]; then
	echo "btrfsck failed - corrupt device?"
	rc=1
else
	rc=0
fi

losetup -d $DEV0
losetup -d $DEV1
losetup -d $DEV2
losetup -d $DEV3
losetup -d $DEV4
rm $TMPIMG0 $TMPIMG1 $TMPIMG2 $TMPIMG3 $TMPIMG4
exit $rc
