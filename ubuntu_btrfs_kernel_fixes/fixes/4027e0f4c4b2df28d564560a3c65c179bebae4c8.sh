#!/bin/bash
cat << EOF
fix 4027e0f4c4b2df28d564560a3c65c179bebae4c8

    Btrfs: clear compress-force when remounting with compress option

EOF

echo "MNT=$MNT"
echo "TMP=$TMP"

TMPIMG=$TMP/test.img
DEV=/dev/loop0

truncate --size 1500m $TMPIMG
losetup $DEV $TMPIMG

echo "mkfs $DEV"
mkfs.btrfs -f $DEV >/dev/null

mount $DEV $MNT -o compress-force=lzo
if [ $? -ne 0 ]; then
	losetup -d $DEV
	rm $TMPIMG
	echo "mount $DEV $MNT failed"
	exit 1
fi

mount $DEV $MNT -o remount,compress=zlib
if [ $? -ne 0 ]; then
	umount $DEV
	losetup -d $DEV
	rm $TMPIMG
	echo "mount $DEV $MNT failed"
	exit 1
fi

n=$(cat /proc/mounts | grep $DEV | grep "compress-force=zlib" | wc -l)

umount $DEV
losetup -d $DEV
rm $TMPIMG

if [ $n -eq 0 ]; then
	echo "compress-force=zlib cleared in remount"
	exit 0
else
	echo "compress-force=zlib NOT cleared in remount"
	exit 1
fi
