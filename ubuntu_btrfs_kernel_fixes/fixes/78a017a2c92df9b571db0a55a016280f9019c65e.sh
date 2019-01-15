#!/bin/bash
cat << EOF
fix 78a017a2c92df9b571db0a55a016280f9019c65e

    Btrfs: add missing compression property remove in btrfs_ioctl_setflags

    The behaviour of a 'chattr -c' consists of getting the current flags,
    clearing the FS_COMPR_FL bit and then sending the result to the set
    flags ioctl - this means the bit FS_NOCOMP_FL isn't set in the flags
    passed to the ioctl. This results in the compression property not being
    cleared from the inode - it was cleared only if the bit FS_NOCOMP_FL
    was set in the received flags.

EOF

TMPIMG=$TMP/test.img
DEV=`losetup -f`

truncate --size 256M $TMPIMG
losetup $DEV $TMPIMG

mkfs.btrfs -f "$DEV" >& /dev/null
if [ $? -ne 0 ]; then
	losetup -d $DEV
	rm -f $TMPIMG
	echo "mkfs.btrfs on $DEV failed"
	exit 1
fi
mount "$DEV" "$MNT"
if [ $? -ne 0 ]; then
	losetup -d $DEV
	rm -f $TMPIMG
	echo "mount $DEV $MNT failed"
	exit 1
fi

rc=0

cd $MNT
mkdir a
chattr +c a
touch a/file
attr=$(lsattr -l a/file | awk '{$1=""; print $0}')
if [ "$attr" != " Compression_Requested" ]; then
	echo "Incorrect attributes on file, got: $attr"
	rc=1
fi

chattr -c a
touch a/file2
attr=$(lsattr -l a/file2 | awk '{$1=""; print $0}')
if [ "$attr" != " ---" ]; then
	echo "Incorrect attributes on file2, got: $attr"
	rc=1
fi
attr=$(lsattr -d -l a | awk '{$1=""; print $0}')
if [ "$attr" != " ---" ]; then
	echo "Incorrect attributes on directory, got: $attr"
	rc=1
fi
cd - >& /dev/null

umount $DEV
losetup -d $DEV
rm -f $TMPIMG
exit $rc
