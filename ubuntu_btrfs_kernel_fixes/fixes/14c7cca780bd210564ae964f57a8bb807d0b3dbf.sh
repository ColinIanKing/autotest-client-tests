#!/bin/bash
cat << EOF
fix 14c7cca780bd210564ae964f57a8bb807d0b3dbf

    Btrfs: fix an oops when deleting snapshots

    We can reproduce this oops via the following steps:

    $ mkfs.btrfs /dev/sdb7
    $ mount /dev/sdb7 /mnt/btrfs
    $ for ((i=0; i<3; i++)); do btrfs sub snap /mnt/btrfs /mnt/btrfs/s_$i; done
    $ rm -fr /mnt/btrfs/*
    $ rm -fr /mnt/btrfs/*

    then we'll get
    ------------[ cut here ]------------
    kernel BUG at fs/btrfs/inode.c:2264!
    [...]

EOF

TMPIMG0=$TMP/test0.img

DEV0=`losetup -f`

truncate --size 512M $TMPIMG0

losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

mount $DEV0 $MNT >& /dev/null

for ((i=0; i<3; i++)); do btrfs sub snap $MNT $MNT/s_$i; done
rm -fr $MNT/btrfs/*
rm -fr $MNT/btrfs/*

dmesg -c > /dev/null
n=$(dmesg | grep "BUG" | wc -l)
if [ $n -gt 0 ]; then
	echo "Found kernel BUG"
	dmesg
	umount $MNT >& /dev/null
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit 0
