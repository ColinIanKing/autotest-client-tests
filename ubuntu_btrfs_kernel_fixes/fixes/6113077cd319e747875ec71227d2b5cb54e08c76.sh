#!/bin/bash
cat << EOF
fix 6113077cd319e747875ec71227d2b5cb54e08c76

    Btrfs: fix missing qgroup reservation before fallocating

    Steps to reproduce:
        mkfs.btrfs <disk>
        mount <disk> <mnt>
        btrfs quota enable <mnt>
        btrfs sub create <mnt>/subv
        btrfs qgroup limit 10M <mnt>/subv
        fallocate --length 20M <mnt>/subv/data

    For the above example, fallocating will return successfully which
    is not expected, we try to fix it by doing qgroup reservation before
    fallocating.

EOF

TMPIMG0=$TMP/test0.img
DEV0=`losetup -f`

truncate --size 512M $TMPIMG0
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
	echo "mount $DEV0 $MNT failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

btrfs quota enable $MNT
btrfs sub create $MNT/subv
btrfs qgroup limit 10M $MNT/subv
#
# fallocate should fail
#
fallocate --length 20M $MNT/subv/data
rc=$?

umount $DEV0
if [ $rc -eq 0 ]; then
	echo "fallocate should have failed, but it did not"
	rc=1
else
	rc=0
fi

losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
