#!/bin/bash
cat << EOF
fix 51a60253a58514524b7a347c4e68553821a79d04

    Btrfs: send, fix incorrect ref access when using extrefs

    When running send, if an inode only has extended reference items
    associated to it and no regular references, send.c:get_first_ref()
    was incorrectly assuming the reference it found was of type
    BTRFS_INODE_REF_KEY due to use of the wrong key variable.
    This caused weird behaviour when using the found item has a regular
    reference, such as weird path string, and occasionally (when lucky)
    a crash.

EOF

TMPIMG=$TMP/test.img
DEV=/dev/loop0

truncate --size 256M $TMPIMG
losetup $DEV $TMPIMG

mkfs.btrfs -f "$DEV" >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs on $DEV failed"
	losetup -d $DEV
	rm -f $TMPIMG
	exit 1
fi
mount "$DEV" "$MNT" -o commit=999
if [ $? -ne 0 ]; then
	echo "mount $DEV $MNT failed"
	losetup -d $DEV
	rm -f $TMPIMG
	exit 1
fi

mkdir $MNT/testdir
touch $MNT/testdir/foobar

for i in `seq 1 2550`; do
	ln $MNT/testdir/foobar $MNT/testdir/foobar_link_`printf "%04d" $i`
done

ln $MNT/testdir/foobar $MNT/testdir/final_foobar_name

rm -f $MNT/testdir/foobar
for i in `seq 1 2550`; do
	rm -f $MNT/testdir/foobar_link_`printf "%04d" $i`
done

umount $DEV
losetup -d $DEV
rm -f $TMPIMG
exit 0
