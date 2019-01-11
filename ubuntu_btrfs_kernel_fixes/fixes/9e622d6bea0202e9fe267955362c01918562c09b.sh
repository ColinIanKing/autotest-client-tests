#!/bin/bash
cat << EOF
fix 9e622d6bea0202e9fe267955362c01918562c09b

    Btrfs: fix enospc error caused by wrong checks of the chunk

    When we did sysbench test for inline files, enospc error happened easily though
    there was lots of free disk space which could be allocated for new chunks.

EOF

TMPIMG0=$TMP/test0.img

DEV0=`losetup -f`

truncate --size 2G $TMPIMG0
losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

ls -al $MNT

mount $DEV0 $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

ulimit -n 102400


dmesg -c > /dev/null
cd $MNT
pwd
sysbench --num-threads=1 --test=fileio --file-num=81920 \
--file-total-size=80M --file-block-size=1K --file-io-mode=sync \
--file-test-mode=seqwr prepare

sysbench --num-threads=1 --test=fileio --file-num=81920 \
> --file-total-size=80M --file-block-size=1K --file-io-mode=sync \
> --file-test-mode=seqwr run

cd - $MNT

n=$(dmesg | grep "BUG" | wc -l)
if [ $n -gt 0 ]; then
	echo "failed, found kernel BUG"
	dmesg
	rc=1
else
	rc=0
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
