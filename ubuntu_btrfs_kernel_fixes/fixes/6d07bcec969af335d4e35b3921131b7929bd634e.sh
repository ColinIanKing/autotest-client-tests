#!/bin/bash
cat << EOF
fix 6d07bcec969af335d4e35b3921131b7929bd634e

    btrfs: fix wrong free space information of btrfs

    When we store data by raid profile in btrfs with two or more different size
    disks, df command shows there is some free space in the filesystem, but the
    user can not write any data in fact, df command shows the wrong free space
    information of btrfs.

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img

DEV0=/dev/loop0
DEV1=/dev/loop1

truncate --size 1G $TMPIMG0
truncate --size 1G $TMPIMG1

losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1

mkfs.btrfs -f -d raid1 $DEV0 $DEV1 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f raid1 $DEV0 $DEV1 failed"
	losetup -d $DEV0
	losetup -d $DEV1
	rm $TMPIMG0 $TMPIMG1
	exit 1
fi

btrfs filesystem show

echo "Empty device:"
btrfs device scan $DEV0 $DEV1
echo ""

mount $DEV0 $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT failed"
	losetup -d $DEV0
	losetup -d $DEV1
	rm $TMPIMG0 $TMPIMG1
	exit 1
fi

dd if=/dev/zero of=$MNT/tmpfile0 bs=4K count=99999999999999 >& /dev/null
sync

echo "df reports:"
df
echo ""
pc=$(df -TH | grep $DEV0 | awk '{ print $6 + 0 }')

echo "Full device:"
btrfs filesystem show
echo ""

if [ $pc -lt 99 ]; then
	echo "Volume should be full, but only $pc is used according to df"
	rc=1
else
	echo "Volume looks full or almost full according to df"
	rc=0
fi
echo ""

umount $MNT >& /dev/null
losetup -d $DEV0
losetup -d $DEV1
rm $TMPIMG0 $TMPIMG1
exit $rc
