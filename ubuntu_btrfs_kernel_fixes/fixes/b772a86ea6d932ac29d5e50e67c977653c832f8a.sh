#!/bin/bash
cat << EOF
fix b772a86ea6d932ac29d5e50e67c977653c832f8a

    Btrfs: fix oops when calling statfs on readonly device

    To reproduce this bug:

      # dd if=/dev/zero of=img bs=1M count=256
      # mkfs.btrfs img
      # losetup -r /dev/loop1 img
      # mount /dev/loop1 /mnt
      OOPS!!

    It triggered BUG_ON(!nr_devices) in btrfs_calc_avail_data_space().
    [ ... ]

EOF

TMPIMG0=$TMP/test0.img
DEV0=/dev/loop0

dd if=/dev/zero of=$TMPIMG0 bs=1M count=256

mkfs.btrfs $TMPIMG0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 failed"
	losetup -d $DEV0
	rm $TMPIMG0
	exit 1
fi

losetup -r $DEV0 $TMPIMG0
dmesg -c > /dev/null
mount $DEV0 $MNT >& /dev/null

n=$(dmesg | grep "BUG" | wc -l)
if [ $n -ne -0 ]; then
	echo "Found kernel BUG"
	dmesg
	umount $MNT
	losetup -d $DEV0
	rm $TMPIMG0
	exit 1
fi

umount $MNT
losetup -d $DEV0
rm $TMPIMG0
exit 0
