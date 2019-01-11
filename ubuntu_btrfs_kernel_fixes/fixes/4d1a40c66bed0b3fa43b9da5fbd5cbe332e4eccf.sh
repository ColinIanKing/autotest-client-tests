#!/bin/bash
cat << EOF
fix 4d1a40c66bed0b3fa43b9da5fbd5cbe332e4eccf

    Btrfs: fix up bounds checking in lseek

    An user reported this, it is because that lseek's SEEK_SET/SEEK_CUR/SEEK_END
    allow a negative value for @offset, but btrfs's SEEK_DATA/SEEK_HOLE don't
    prepare for that and convert the negative @offset into unsigned type,
    so we get (end < start) warning.
EOF

gcc ${FIX}.c -o ${FIX}.out
if [ $? -ne 0 ]; then
	echo "Failed to build ${FIX}.c"
	exit 1
fi

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
mount "$DEV" "$MNT" -o compress=lzo
if [ $? -ne 0 ]; then
	losetup -d $DEV
	rm -f $TMPIMG
	echo "mount $DEV $MNT failed"
	exit 1
fi

${FIX}.out $MNT/seekfile
rc=$?

umount $DEV
losetup -d $DEV
rm -f $TMPIMG ${FIX}.out
exit $rc
