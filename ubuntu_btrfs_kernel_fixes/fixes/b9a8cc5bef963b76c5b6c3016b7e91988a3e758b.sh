#!/bin/bash
cat << EOF
fix b9a8cc5bef963b76c5b6c3016b7e91988a3e758b

    Btrfs: fix file extent discount problem in the, snapshot

    If a snapshot is created while we are writing some data into the file,
    the i_size of the corresponding file in the snapshot will be wrong, it will
    be beyond the end of the last file extent. And btrfsck will report:
      root 256 inode 257 errors 100

    Steps to reproduce:
     # mkfs.btrfs <partition>
     # mount <partition> <mnt>
     # cd <mnt>
     # dd if=/dev/zero of=tmpfile bs=4M count=1024 &
     # for ((i=0; i<4; i++))
     > do
     > btrfs sub snap . $i
     > done

EOF

TMPIMG0=$TMP/test0.img
DEV0=`losetup -f`

truncate --size 512M $TMPIMG0
losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs $DEV0 failed"
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

dd if=/dev/zero of=$MNT/tmpfile bs=4M count=1024 &
pid=$!

for ((i=0; i<4; i++))
do
	btrfs sub snap $MNT $MNT/$i
done
kill -9 $pid
wait $pid

umount $DEV0
n=$(btrfsck $DEV0 | grep "errors")
if [ $n -gt 0 ]; then
	echo "failed, btrfsck found some errors"
	rc=1
else
	rc=0
fi

losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
