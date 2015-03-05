#!/bin/bash
cat << EOF
fix 9dced186f934648bb7796ad3301cfc2563e2ad6e

    Btrfs: fix the free space write out failure when there is no data space

    After running space balance on a new fs, the fs check program outputed the
    following warning message:
     free space inode generation (0) did not match free space cache generation (20)

    Steps to reproduce:
     # mkfs.btrfs -f <dev>
     # mount <dev> <mnt>
     # btrfs balance start <mnt>
     # umount <mnt>
     # btrfs check <dev>

    [...]

EOF

TMPIMG0=$TMP/test0.img

DEV0=/dev/loop0

truncate --size 512M $TMPIMG0

losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0  >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 failed"
	losetup -d $DEV0
	rm $TMPIMG0
	exit 1
fi

mount $DEV0 $MNT
btrfs balance start $MNT
umount $MNT
rc=0
n=$(btrfs check $DEV0 | grep "did not match free space cache generation" | wc -l)
if [ $n -gt 0 ]; then
	echo "btrfs check reported unexecpted free space cache generation message"
	rc=1
fi

losetup -d $DEV0
rm $TMPIMG0
exit $rc
