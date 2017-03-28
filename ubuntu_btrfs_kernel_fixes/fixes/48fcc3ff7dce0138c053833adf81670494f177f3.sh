#!/bin/bash
cat << EOF
fix 48fcc3ff7dce0138c053833adf81670494f177f3

    btrfs: label should not contain return char

    Rediffed remaining parts of original patch from Anand Jain.  This makes
    sure to avoid trailing newlines in the btrfs label output

EOF

echo "MNT=$MNT"
echo "TMP=$TMP"

TMPIMG=$TMP/test.img
DEV=/dev/loop0

truncate --size 1500m $TMPIMG
losetup $DEV $TMPIMG

echo "mkfs $DEV"
mkfs.btrfs -f $DEV >/dev/null

UUID=$(btrfs fi show $DEV | head -1 | sed -e 's/.*uuid: \([-0-9a-z]*\)$/\1/')

echo "mount $DEV $MNT"
mount "$DEV" "$MNT"
if [ $? -ne 0 ]; then
	rm -f $TMPIMG
	losetup -d $DEV
	echo "mount $DEV $MNT failed"
	exit 1
fi

LABELFILE=/sys/fs/btrfs/$UUID/label

if [ ! -e $LABELFILE ]; then
	echo "Cannot test, $LABELFILE does not exist"
	umount $DEV
	losetup -d $DEV
	rm -f $TMPIMG
	exit 2
fi

echo "Test for empty label..."
LINES="$(cat $LABELFILE | wc -l | awk '{print $1}')"
RET=0

if [ $LINES -eq 0 ] ; then
	echo 'PASS: Trailing \n is removed correctly.'
else
	echo 'FAIL: Trailing \n still exists.'
	RET=1
fi

echo "Test for non-empty label..."

echo testlabel >$LABELFILE
LINES="$(cat $LABELFILE | wc -l | awk '{print $1}')"

if [ $LINES -eq 1 ] ; then
	echo 'PASS: Trailing \n is removed correctly.'
else
        echo 'FAIL: Trailing \n still exists.'
        RET=1
fi

umount $DEV
losetup -d $DEV
rm -f $TMPIMG
exit $RET
