#!/bin/bash
cat << EOF
fix 1104a8855109a4051d74977f819a13b4516aa11e

    btrfs: enhance superblock checks

    The superblock checksum is not verified upon mount. <awkward silence>

    Add that check and also reorder existing checks to a more logical
    order.

    Current mkfs.btrfs does not calculate the correct checksum of
    super_block and thus a freshly created filesytem will fail to mount when
    this patch is applied.

    First transaction commit calculates correct superblock checksum and
    saves it to disk.

    Reproducer:
    $ mfks.btrfs /dev/sda
    $ mount /dev/sda /mnt
    $ btrfs scrub start /mnt
    $ sleep 5
    $ btrfs scrub status /mnt
    ... super:2 ...

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

mount $DEV0 $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT -o failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

btrfs scrub start $MNT
sleep 5
btrfs scrub status $MNT

rc=0

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
