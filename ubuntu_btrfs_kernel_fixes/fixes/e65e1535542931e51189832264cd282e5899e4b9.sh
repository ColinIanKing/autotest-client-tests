#!/bin/bash
cat << EOF
fix e65e1535542931e51189832264cd282e5899e4b9

    btrfs: fix panic caused by direct IO

    btrfs paniced when we write >64KB data by direct IO at one time.

    Reproduce steps:
     # mkfs.btrfs /dev/sda5 /dev/sda6
     # mount /dev/sda5 /mnt
     # dd if=/dev/zero of=/mnt/tmpfile bs=100K count=1 oflag=direct

    Then btrfs paniced:
    mapping failed logical 1103155200 bio len 69632 len 12288
    ------------[ cut here ]------------
    kernel BUG at fs/btrfs/volumes.c:3010!
    [....]

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img

DEV0=/dev/loop0
DEV1=/dev/loop1

truncate --size 512M $TMPIMG0
truncate --size 512M $TMPIMG1

losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1

mkfs.btrfs -f $DEV0 $DEV1 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 failed"
	losetup -d $DEV0 $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	exit 1
fi

mount $DEV0 $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT failed"
	losetup -d $DEV0 $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	exit 1
fi

dmesg -c > /dev/null
dd if=/dev/zero of=$MNT/tmpfile bs=100K count=1 oflag=direct >& /dev/null
if [ $? -ne 0 ]; then
	echo "direct I/O dd if=/dev/zero of=$MNT/tmpfile bs=100K count=1 oflag=direct failed"
	umount $MNT >& /dev/null
	losetup -d $DEV0 $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	exit 1
fi
n=$(dmesg | grep "BUG" | wc -l)
if [ $n -gt 0 ]; then
	echo "detected kernel BUG on direct I/O dd"
	dmesg
	umount $MNT >& /dev/null
	losetup -d $DEV0 $DEV1
	rm -f $TMPIMG0 $TMPIMG1
fi
umount $MNT >& /dev/null
losetup -d $DEV0 $DEV1
rm -f $TMPIMG0 $TMPIMG1

exit 0
