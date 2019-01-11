#!/bin/bash
cat << EOF
fix 5762b5c958abbecb7fb9f4596a6476d1ce91ecf6

    Btrfs: ensure tmpfile inode is always persisted with link count of 0

    If we open a file with O_TMPFILE, don't do any further operation on
    it (so that the inode item isn't updated) and then force a transaction
    commit, we get a persisted inode item with a link count of 1, and not 0
    as it should be.

EOF

do_info() {
	for I in $*
	do
		if [ "$I" == "links" ]; then
			shift
			echo $1
			return
		fi
		shift
	done
}


rm -f ${FIX}.out
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

${FIX}.out $MNT &
pid=$!
sleep 2
info=$(btrfs-debug-tree $DEV | grep "size 1048576")
links=$(do_info $info)

echo "Found $links links on a O_TMPFILE temp file (should be 0)"

kill -SIGUSR1 $pid
sleep 1

umount $DEV
losetup -d $DEV
rm -f $TMPIMG ${FIX}.out
exit $links
