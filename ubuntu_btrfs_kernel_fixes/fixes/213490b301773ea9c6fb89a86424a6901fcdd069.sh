#!/bin/bash
cat << EOF
fix 213490b301773ea9c6fb89a86424a6901fcdd069

    Btrfs: fix a bug of per-file nocow

   Users report a bug, the reproducer is:
    $ mkfs.btrfs /dev/loop0
    $ mount /dev/loop0 /mnt/btrfs/
    $ mkdir /mnt/btrfs/dir
    $ chattr +C /mnt/btrfs/dir/
    $ dd if=/dev/zero of=/mnt/btrfs/dir/foo bs=4K count=10;
    $ lsattr /mnt/btrfs/dir/foo
    ---------------C- /mnt/btrfs/dir/foo
    $ filefrag /mnt/btrfs/dir/foo
    /mnt/btrfs/dir/foo: 1 extent found    ---> an extent
    $ dd if=/dev/zero of=/mnt/btrfs/dir/foo bs=4K count=1 seek=5 conv=notrunc,nocreat; sync
    $ filefrag /mnt/btrfs/dir/foo
    /mnt/btrfs/dir/foo: 3 extents found   ---> with nocow, btrfs breaks the extent into three parts

    The new created file should not only inherit the NODATACOW flag, but also
    honor NODATASUM flag, because we must do COW on a file extent with checksum.

EOF

TMPIMG0=$TMP/test0.img
DEV0=`losetup -f`
truncate --size 256M $TMPIMG0
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
	echo "mount $DEV0 $MNT -o failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

rc=0
mkdir $MNT/dir
chattr +C $MNT/dir
dd if=/dev/zero of=$MNT/dir/foo bs=4K count=10 >& /dev/null
lsattr $MNT/dir/foo
# ---------------C- /mnt/btrfs/dir/foo
filefrag $MNT/dir/foo
e1=$(filefrag $MNT/dir/foo | awk '{ print $2}')
if [ $e1 -ne 1 ]; then
	echo "expecting 1 extent, got $e1"
	rc=1
fi
# /mnt/btrfs/dir/foo: 1 extent found    ---> an extent
dd if=/dev/zero of=$MNT/dir/foo bs=4K count=1 seek=5 conv=notrunc,nocreat >& /dev/null
sync
e2=$(filefrag $MNT/dir/foo | awk '{ print $2}')
filefrag $MNT/dir/foo
# /mnt/btrfs/dir/foo: 3 extents found   --
if [ $e2 -ne 1 ]; then
	echo "expecting 1 extent, got $e2"
	rc=1
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
