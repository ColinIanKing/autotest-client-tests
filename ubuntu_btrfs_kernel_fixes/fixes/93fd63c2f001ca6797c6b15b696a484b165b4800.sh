#!/bin/bash
cat << EOF
fix 93fd63c2f001ca6797c6b15b696a484b165b4800

    Commit 2bc5565286121d2a77ccd728eb3484dff2035b58 (Btrfs: don't update atime on
    RO subvolumes) ensures that the access time of an inode is not updated when
    the inode lives in a read-only subvolume.
    However, if a directory on a read-only subvolume is accessed, the atime is
    updated. This results in a write operation to a read-only subvolume. I
    believe that access times should never be updated on read-only subvolumes.

EOF

TMPIMG0=$TMP/test0.img

DEV0=/dev/loop0

truncate --size 2G $TMPIMG0
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

btrfs subvol create $MNT/sub
mkdir $MNT/sub/dir
echo "abc" > $MNT/sub/dir/file
btrfs subvol snapshot -r $MNT/sub $MNT/rosnap
stat $MNT/rosnap/dir > $TMP/stat.pre
sleep 1.0
ls $MNT/rosnap/dir
stat $MNT/rosnap/dir > $TMP/stat.post

echo ""
echo "Before access of file:"
cat $TMP/stat.pre
echo ""
echo "After access of file:"
cat $TMP/stat.post
echo ""

diff $TMP/stat.pre $TMP/stat.post
if [ $? -ne 0 ]; then
	echo "access time on read omly subvolume was updated which is a bug"
	rc=1
else
	echo "access time on read-only subvolume was not updated as expected"
	rc=0
fi

umount $DEV0 >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0 $TMP/stat.pre $TMP/stat.post
exit $rc
