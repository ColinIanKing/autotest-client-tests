#!/bin/bash
cat << EOF
fix f70a9a6b94af86fca069a7552ab672c31b457786

    Btrfs: fix btrfsck error 400 when truncating a compressed

    Reproduce steps:
     # mkfs.btrfs /dev/sdb5
     # mount /dev/sdb5 -o compress=lzo /mnt
     # dd if=/dev/zero of=/mnt/tmpfile bs=128K count=1
     # sync
     # truncate -s 64K /mnt/tmpfile
     root 5 inode 257 errors 400

    This is because of the wrong if condition, which is used to check if we should
    subtract the bytes of the dropped range from i_blocks/i_bytes of i-node or not.
    When we truncate a compressed extent, btrfs substracts the bytes of the whole
    extent, it's wrong. We should substract the real size that we truncate, no
    matter it is a compressed extent or not. Fix it.

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

mount $DEV0 -o compress=lzo $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 -o compress=lzo $MNT failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

dd if=/dev/zero of=$MNT/tmpfile bs=128K count=1
sync
truncate -s 64K $MNT/tmpfile
umount $MNT >& /dev/null
btrfsck $DEV0
rc=$?
if [ $rc -ne 0 ]; then
	echo "btrfsck failed, returned error $rc"
	rc=1
fi

losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
