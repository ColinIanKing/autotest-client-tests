#!/bin/bash
cat << EOF
fix 0c1a98c81413e00a6c379d898e06a09350d31926

    Btrfs: fix the file extent gap when doing direct IO

    When we write some data to the place that is beyond the end of the file
    in direct I/O mode, a data hole will be created. And Btrfs should insert
    a file extent item that point to this hole into the fs tree. But unfortunately
    Btrfs forgets doing it.

    The following is a simple way to reproduce it:
     # mkfs.btrfs /dev/sdc2
     # mount /dev/sdc2 /test4
     # touch /test4/a
     # dd if=/dev/zero of=/test4/a seek=8 count=1 bs=4K oflag=direct conv=nocreat,notrunc
     # umount /test4
     # btrfsck /dev/sdc2
     root 5 inode 257 errors 100

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

mount $DEV0 $MNT >& /dev/null

touch $MNT/a
dd if=/dev/zero of=$MNT/a seek=8 count=1 bs=4K oflag=direct conv=nocreat,notrunc
umount $MNT >& /dev/null

#
#  There should be no errors if the file extent is correct
#
errors=$(btrfsck $DEV0 | grep "errors" | wc -l)
if [ $errors -ne -0 ]; then
	echo "btrfsck found some unexpected errors"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

losetup -d $DEV0
rm -f $TMPIMG0
exit 0
