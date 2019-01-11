#!/bin/bash
cat << EOF
fix 66c2689226ac322fbc9acd2e8e418b78dcd52f51

Btrfs: do not bother to defrag an extent if it is a big real extent

EOF

TMPIMG0=$TMP/test0.img

DEV0=`losetup -f`

truncate --size 512M $TMPIMG0
losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

mount $DEV0 $MNT -oautodefrag >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT -oautodefrag failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

dd if=/dev/zero of=$MNT/foobar bs=64k count=40 oflag=direct 2>/dev/null
filefrag -v $MNT/foobar | grep "\.\." | awk '{print $1,$2,$3,$4,$5}' > $TMP/presync
sync
filefrag -v $MNT/foobar | grep "\.\." | awk '{print $1,$2,$3,$4,$5}' > $TMP/postsync
diff $TMP/presync $TMP/postsync
rc=$?
if [ $rc -ne 0 ]; then
	echo "large extents seem to have been degragmented, failed"
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
