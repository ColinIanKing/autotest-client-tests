#!/bin/bash
cat << EOF
fix 9ba1f6e44ed7a1fa52d3f292508bf921b5054172

    Btrfs: do not do balance in readonly mode

    In normal cases, we would not be allowed to do balance in RO mode.
    However, when we're using a seeding device and adding another device to sprout,
    things will change:

    $ mkfs.btrfs /dev/sdb7
    $ btrfstune -S 1 /dev/sdb7
    $ mount /dev/sdb7 /mnt/btrfs -o ro
    $ btrfs fi bal /mnt/btrfs   -----------------------> fail.
    $ btrfs dev add /dev/sdb8 /mnt/btrfs
    $ btrfs fi bal /mnt/btrfs   -----------------------> works!

    It should not be designed as an exception, and we'd better add another check for
    mnt flags.

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img

truncate --size 512M $TMPIMG0
truncate --size 512M $TMPIMG1

DEV0=`losetup -f`
losetup $DEV0 $TMPIMG0

DEV1=`losetup -f`
losetup $DEV1 $TMPIMG1

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 failed"
	losetup -d $DEV0
	losetup -d $DEV1
	rm -f $TMPIMG0
	exit 1
fi
btrfstune -S 1 $DEV0

mount $DEV0 $MNT -o ro >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT -o ro failed"
	losetup -d $DEV0
	losetup -d $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	exit 1
fi

rc=0
btrfs fi bal $MNT >& /dev/null
r1=$?
if [ $r1 -eq 0 ]; then
	echo "failed: allowed to rebalance read only filesystem"
	rc=1
else
	echo "passed, not allowed to rebalance read only filesystem"
fi
echo ""
btrfs dev add $DEV1 $MNT
btrfs fi bal $MNT >& /dev/null
r2=$?
if [ $r2 -eq 0 ]; then
	echo "failed: allowed to rebalance read only filesystem after r/w device added"
	rc=1
else
	echo "passed, not allowed to rebalance read only filesystem after r/w device added"
fi

umount $DEV0
losetup -d $DEV0
losetup -d $DEV1
rm -f $TMPIMG0 $TMPIMG1
exit $rc
