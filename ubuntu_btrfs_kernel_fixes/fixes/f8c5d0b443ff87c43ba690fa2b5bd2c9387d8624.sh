#!/bin/bash
cat << EOF
fix f8c5d0b443ff87c43ba690fa2b5bd2c9387d8624

    Btrfs: fix wrong error returned by adding a device

    [...]

    Since we mount with readonly options, and /dev/sdb7 is not a seeding one,
    a readonly notification is preferred.

    Signed-off-by: Liu Bo <liubo2009@cn.fujitsu.com>
    Reviewed-by: Josef Bacik <josef@redhat.com>

EOF

TMPIMG0=$TMP/test0.img
TMPIMG1=$TMP/test1.img
DEV0=/dev/loop0
DEV1=/dev/loop1

truncate --size 256M $TMPIMG0
truncate --size 256M $TMPIMG1
losetup $DEV0 $TMPIMG0
losetup $DEV1 $TMPIMG1

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs $DEV0 failed"
	losetup -d $DEV0
	losetup -d $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	exit 1
fi

mount $DEV0 $MNT -o ro >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT -ro failed"
	losetup -d $DEV0
	losetup -d $DEV1
	rm -f $TMPIMG0 $TMPIMG1
	exit 1
fi

btrfs dev add $DEV1 $MNT 2> $TMP/stderr.out
rc=$?

echo "Got error message:"
cat $TMP/stderr.out
echo " "

if [ $rc -eq 0 ]; then
	echo "Expected btrfs dev add $DEV1 $MNT to fail and it didn't"
	rc=1
else
	n=$(grep "Read-only file system" $TMP/stderr.out | wc -l)
	if [ $n -eq 0 ]; then
		echo "Expecting an error message complaining about a Read-only file system, but didn't get one"
		rc=1
	else
		rc=0
	fi
fi

umount $DEV0

losetup -d $DEV0
losetup -d $DEV1
rm -f $TMPIMG0 $TMPIMG1
exit $rc
