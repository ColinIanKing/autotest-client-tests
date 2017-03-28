#!/bin/bash
cat << EOF
fix 9a40f1222a372de77344d85d31f8fe0e1c0e60e7

    btrfs: filter invalid arg for btrfs resize

    Originally following cmds will work:
        # btrfs fi resize -10A  <mnt>
        # btrfs fi resize -10Gaha <mnt>
    Filter the arg by checking the return pointer of memparse.

EOF

TMPIMG=$TMP/test.img
DEV=/dev/loop0

truncate --size 512M $TMPIMG

losetup $DEV $TMPIMG

mkfs.btrfs -f $DEV  >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV  >& /dev/null failed"
	losetup -d $DEV
	rm -f $TMPIMG
	exit 1
fi

mount $DEV $MNT
if [ $? -ne 0 ]; then
	echo "mount $DEV $MNT failed"
	losetup -d $DEV
	rm -f $TMPIMG
	exit 1
fi

rc=0
#
# Test that the following FAIL
#
btrfs fi resize -10A $MNT >& /dev/null
if [ $? -eq 0 ]; then
	echo "btrfs fi resize -10A $MNT did not fail as expected"
	rc=1
fi
btrfs fi resize -10Gaha $MNT >& /dev/null
if [ $? -eq 0 ]; then
	echo "btrfs fi resize -10Gaha $MNT did not fail as expected"
	rc=1
fi

umount $MNT
losetup -d $DEV
rm -f $TMPIMG
exit $rc
