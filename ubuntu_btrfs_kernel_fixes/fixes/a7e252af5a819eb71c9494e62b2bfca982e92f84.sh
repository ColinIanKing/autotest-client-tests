#!/bin/bash
cat << EOF
fix a7e252af5a819eb71c9494e62b2bfca982e92f84

    Btrfs: don't clear the default compression type

    [...]

    Steps to reproduce:
     # mkfs.btrfs -f <dev>
     # mount -o nodatacow <dev> <mnt>
     # touch <mnt>/<file>
     # chattr =c <mnt>/<file>
     # dd if=/dev/zero of=<mnt>/<file> bs=1M count=10

    It is because we cleared the default compression type when setting the
    nodatacow. In fact, we needn't do it because we have used COMPRESS flag to
    indicate if we need compressed the file data or not, needn't use the
    variant -- compress_type -- in btrfs_info to do the same thing, and just
    use it to hold the default compression type. Or we would get a wrong compress
    type for a file whose own compress flag is set but the compress flag of its
    filesystem is not set.

EOF

TMPIMG0=$TMP/test0.img

DEV0=/dev/loop0

truncate --size 512M $TMPIMG0

losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0  >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

dmesg -c > /dev/null
mount -o nodatacow $DEV0 $MNT
touch $MNT/file
chattr -c $MNT/file
dd if=/dev/zero of=$MNT/file bs=1M count=10 >& /dev/null

#
# Anything blow up?
#
dumped=$(dmesg | grep "BUG" | wc -l)
if [ $dumped -gt 0 ]; then
	echo "found a kernel BUG"
	dmesg
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
