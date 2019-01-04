#!/bin/bash
cat << EOF
fix 5fbc7c59fd22c5a6531b40b0759624b680a95e52

    Btrfs: fix unfinished readahead thread for raid5/6 degraded mounting

    Steps to reproduce:

     # mkfs.btrfs -f /dev/sd[b-f] -m raid5 -d raid5
     # mkfs.ext4 /dev/sdc --->corrupt one of btrfs device
     # mount /dev/sdb /mnt -o degraded
     # btrfs scrub start -BRd /mnt

    This is because readahead would skip missing device, this is not true
    for RAID5/6, because REQ_GET_READ_MIRRORS return 1 for RAID5/6 block
    mapping. If expected data locates in missing device, readahead thread
    would not call __readahead_hook() which makes event @rc->elems=0
    wait forever.

    Fix this problem by checking return value of btrfs_map_block(),we
    can only skip missing device safely if there are several mirrors.

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

truncate --size 2G $TMPIMG0
truncate --size 2G $TMPIMG1
truncate --size 2G $TMPIMG2
truncate --size 2G $TMPIMG3
truncate --size 2G $TMPIMG4

losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1
losetup $DEV2 $TMPIMG2
losetup $DEV3 $TMPIMG3
losetup $DEV4 $TMPIMG4

mkfs.btrfs -f -m raid5 -d raid5 $DEV0 $DEV1 $DEV2 $DEV3 $DEV4 >& /dev/null
if [ $? -ne 0 ]; then
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	losetup -d $DEV3
	losetup -d $DEV4
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2 $TMPIMG3 $TMPIMG4
	echo "mkfs.btrfs -f -m raid5 -d raid5 $DEV0 $DEV1 $DEV2 $DEV3 $DEV4 $MNT failed"
	exit 1
fi

#
# Corrupt one of the devices
#
mkfs.ext4 -F $DEV1

mount -o degraded $DEV0 $MNT
if [ $? -eq 1 ]; then
	echo "mount $DEV0 on degraded raid5 failed"
	losetup -d $DEV0
	losetup -d $DEV1
	losetup -d $DEV2
	losetup -d $DEV3
	losetup -d $DEV4
	rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2 $TMPIMG3 $TMPIMG4
	exit 1
fi

rc=0
btrfs scrub start -BRd $MNT
if [ $? -eq 1 ]; then
	echo "btrfs scrub start on $MNT failed"
	rc=1
fi

umount $MNT
losetup -d $DEV0
losetup -d $DEV1
losetup -d $DEV2
losetup -d $DEV3
losetup -d $DEV4
rm -f $TMPIMG0 $TMPIMG1 $TMPIMG2 $TMPIMG3 $TMPIMG4
exit $rc
