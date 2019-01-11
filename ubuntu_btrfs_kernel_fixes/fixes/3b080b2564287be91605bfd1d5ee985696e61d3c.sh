#!/bin/bash
cat << EOF
fix 3b080b2564287be91605bfd1d5ee985696e61d3c

    Btrfs: scrub raid56 stripes in the right way

    Steps to reproduce:
     # mkfs.btrfs -f /dev/sda[8-11] -m raid5 -d raid5
     # mount /dev/sda8 /mnt
     # btrfs scrub start -BR /mnt
     # echo $? <--unverified errors make return value be 3

    This is because we don't setup right mapping between physical
    and logical address for raid56, which makes checksum mismatch.
    But we will find everthing is fine later when rechecking using
    btrfs_map_block().

    This patch fixed the problem by settuping right mappings and
    we only verify data stripes' checksums.

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img
TMPIMG2=$TMP/test2.img
TMPIMG3=$TMP/test3.img

truncate --size 512M $TMPIMG0
truncate --size 512M $TMPIMG1
truncate --size 512M $TMPIMG2
truncate --size 512M $TMPIMG3

DEV0=`losetup -f`
losetup $DEV0 $TMPIMG0

DEV1=`losetup -f`
losetup $DEV1 $TMPIMG1

DEV2=`losetup -f`
losetup $DEV2 $TMPIMG2

DEV3=`losetup -f`
losetup $DEV3 $TMPIMG3

mkfs.btrfs -f $DEV0 $DEV1 $DEV2 $DEV3 -m raid5 -d raid5 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 $DEV1 $DEV2 $DEV3 -m raid5 -d raid5 failed"
	losetup -d $DEV0 $DEV1 $DEV2 $DEV3
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2 $TMPIMG3
	exit 1
fi

mount $DEV0 $MNT
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT failed"
	losetup -d $DEV0 $DEV1 $DEV2 $DEV3
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2 $TMPIMG3
	exit 1
fi

btrfs scrub start -BR $MNT
rc=$?
if [ $rc -ne 0 ]; then
	echo "btrfs scrub start -BR $MNT failed, return: $rc"
fi

umount $DEV0
losetup -d $DEV0 $DEV1 $DEV2 $DEV3
rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2 $TMPIMG3
exit $rc
