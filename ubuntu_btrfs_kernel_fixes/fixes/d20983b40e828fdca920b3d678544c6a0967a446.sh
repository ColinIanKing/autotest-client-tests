#!/bin/bash
cat << EOF
fix d20983b40e828fdca920b3d678544c6a0967a446

    Btrfs: fix writing data into the seed filesystem
    
    If we mounted a seed filesystem with degraded option, and then added a new
    device into the seed filesystem, then we found adding device failed because
    of the IO failure.
    
    Steps to reproduce:
     # mkfs.btrfs -d raid1 -m raid1 <dev0> <dev1>
     # btrfstune -S 1 <dev0>
     # mount <dev0> -o degraded <mnt>
     # btrfs device add -f <dev2> <mnt>

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img
TMPIMG2=$TMP/test2.img

DEV0=/dev/loop0
DEV1=/dev/loop1
DEV2=/dev/loop2

truncate --size 256M $TMPIMG0
truncate --size 256M $TMPIMG1
truncate --size 256M $TMPIMG2

losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1
losetup $DEV2 $TMPIMG2

if [ $? -ne 0 ]; then

	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
	echo "mkfs.btrfs on $DEV failed"
	exit 1
fi
mkfs.btrfs -f -d raid1 -m raid1 $DEV0 $DEV1 >& /dev/null
btrfstune -S 1 $DEV0 >& /dev/null

mount -t btrfs $DEV0 -o degraded $MNT >& /dev/null
if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
	echo "mount $DEV $MNT failed"
	exit 1
fi

#
# This used to fail, the fix resolves this failure
#
btrfs device add -f $DEV2 $MNT
rc=$?

umount $MNT

losetup -d $DEV0
losetup -d $DEV1
losetup -d $DEV2
rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2
exit $rc
