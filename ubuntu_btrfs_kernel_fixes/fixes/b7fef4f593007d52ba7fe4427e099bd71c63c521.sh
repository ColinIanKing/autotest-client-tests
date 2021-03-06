#!/bin/bash
cat << EOF
fix b7fef4f593007d52ba7fe4427e099bd71c63c521

    Btrfs: fix missing check before creating a qgroup relation

    Step to reproduce:
                mkfs.btrfs <disk>
                mount <disk> <mnt>
                btrfs quota enable <mnt>
                btrfs qgroup assign 0/1 1/1 <mnt>
                umount <mnt>
                btrfs-debug-tree <disk> | grep QGROUP
    If we want to add a qgroup relation, we should gurantee that
    'src' and 'dst' exist, otherwise, such qgroup relation should
    not be allowed to create.

EOF

TMPIMG0=$TMP/test0.img
DEV0=`losetup -f`

truncate --size 1G $TMPIMG0
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

btrfs quota enable $MNT
btrfs qgroup assign 0/1 1/1 $MNT
if [ $? -eq 0 ]; then
    echo "btrfs qgroup relationship assignment should fail for a non-existing src/dst"
    rc=1
else
    echo "btrfs qgroup relationship assignemnt for a non-existing src/dst failed as expected"
    rc=0
fi
umount $MNT >& /dev/null
btrfs-debug-tree $DEV0 | grep QGROUP

losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
