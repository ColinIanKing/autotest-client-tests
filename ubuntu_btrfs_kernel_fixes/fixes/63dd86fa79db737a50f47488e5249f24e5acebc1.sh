#!/bin/bash
cat << EOF
fix 63dd86fa79db737a50f47488e5249f24e5acebc1

    btrfs: fix rw_devices miss match after seed replace
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
	rm $TMPIMG0 $TMPIMG1 $TMPIMG2
	echo "mkfs.btrfs on $DEV failed"
	exit 1
fi
mkfs.btrfs -f "$DEV0" >& /dev/null
mount -t btrfs "$DEV0" "$MNT" -o compress=zlib
if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	rm $TMPIMG0 $TMPIMG1 $TMPIMG2
	echo "mount $DEV $MNT failed"
	exit 1
fi

rc=0

for i in $(seq 32)
do
	dd if=/dev/urandom of=$MNT/random.$i bs=1M count=8
done
df
du

btrfs dev add $DEV1 $MNT
btrfs rep start -B $DEV0 $DEV2 $MNT
umount $MNT
rc=$(dmesg | grep "WARNING" | grep "__btrfs_close_devices" | wc -l)

losetup -d $DEV0
losetup -d $DEV1
losetup -d $DEV2
rm $TMPIMG0 $TMPIMG1 $TMPIMG2
exit $rc
