#!/bin/bash
cat << EOF
fix d52a5b5f1fa40804f681cf9868d4a8f90661bdf3

    btrfs: try to reclaim some space when chunk allocation fails

    We cannot write data into files when when there is tiny space in the filesystem.

    Reproduce steps:
     # mkfs.btrfs /dev/sda1
     # mount /dev/sda1 /mnt
     # dd if=/dev/zero of=/mnt/tmpfile0 bs=4K count=1
     # dd if=/dev/zero of=/mnt/tmpfile1 bs=4K count=99999999999999
       (fill the filesystem)
     # umount /mnt
     # mount /dev/sda1 /mnt
     # rm -f /mnt/tmpfile0
     # dd if=/dev/zero of=/mnt/tmpfile0 bs=4K count=1
       (failed with nospec)

EOF

TMPIMG0=$TMP/test0.img

DEV0=/dev/loop0

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
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

dd if=/dev/zero of=$MNT/tmpfile0 bs=4K count=1
#
# Fill the system
#
dd if=/dev/zero of=$MNT/tmpfile1 bs=4K count=99999999999999
umount $MNT
mount /dev/sda1 $MNT
rm -f $MNT/tmpfile0
dd if=/dev/zero of=$MNT/tmpfile0 bs=4K count=1
rc=$?
if [ $rc -ne 0 ]; then
	echo "could not dd small 4K file"
	rc=1
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
