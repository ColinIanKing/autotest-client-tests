#!/bin/bash
cat << EOF
fix f0dd9592a1aa014b3a01aa2be7e795aae040d65b

    Btrfs: fix direct-io vs nodatacow

    To reproduce the bug:

      # mount -o nodatacow /dev/sda7 /mnt/
      # dd if=/dev/zero of=/mnt/tmp bs=4K count=1
      1+0 records in
      1+0 records out
      4096 bytes (4.1 kB) copied, 0.000136115 s, 30.1 MB/s
      # dd if=/dev/zero of=/mnt/tmp bs=4K count=1 conv=notrunc oflag=direct
      dd: writing '/mnt/tmp': Input/output error
      1+0 records in
      0+0 records out

    btrfs_ordered_update_i_size() may return 1, but btrfs_endio_direct_write()
    mistakenly takes it as an error.

EOF

TMPIMG0=$TMP/test0.img
DEV0=`losetup -f`

truncate --size 256M $TMPIMG0

losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs $DEV0 failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

mount -o nodatacow $DEV0 $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi
dd if=/dev/zero of=$TMP/tmp bs=4K count=1
dd if=/dev/zero of=$TMP/tmp bs=4K count=1 conv=notrunc oflag=direct
if [ $? -ne 0 ]; then
	echo "dd should succeed with conv=notrunc oflag=direct but it failed"
	rc=1
else
	rc=0
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
