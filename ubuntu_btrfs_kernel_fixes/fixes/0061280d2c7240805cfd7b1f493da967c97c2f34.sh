#!/bin/bash
cat << EOF
fix 0061280d2c7240805cfd7b1f493da967c97c2f34

    Btrfs: fix the page that is beyond EOF

    Steps to reproduce:
     # mkfs.btrfs <disk>
     # mount <disk> <mnt>
     # dd if=/dev/zero of=<mnt>/<file> bs=512 seek=5 count=8
     # fallocate -p -o 2048 -l 16384 <mnt>/<file>
     # dd if=/dev/zero of=<mnt>/<file> bs=4096 seek=3 count=8 conv=notrunc,nocreat
     # umount <mnt>
     # dmesg
     WARNING: at fs/btrfs/inode.c:7140 btrfs_destroy_inode+0x2eb/0x330

    The reason is that we inputed a range which is beyond the end of the file. And
    because the end of this range was not page-aligned, we had to truncate the last
    page in this range, this operation is similar to a buffered file write. In other
    words, we reserved enough space and clear the data which was in the hole range
    on that page. But when we expanded that test file, write the data into the same
    page, we forgot that we have reserved enough space for the buffered write of
    that page because in most cases there is no page that is beyond the end of
    the file. As a result, we reserved the space twice.

    In fact, we needn't truncate the page if it is beyond the end of the file, just
    release the allocated space in that range. Fix the above problem by this way.

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

dmesg -c > /dev/null
dd if=/dev/zero of=$MNT/file bs=512 seek=5 count=8 >& /dev/null
fallocate -p -o 2048 -l 16384 $MNT/file
dd if=/dev/zero of=$MNT/file bs=4096 seek=3 count=8 conv=notrunc,nocreat >& /dev/null
umount $MNT
n=$(dmesg | grep "WARNING:" | wc -l)
rc=0
if [ $n -gt 0 ]; then
	echo "Found kernel WARNING"
	dmesg
	rc=1
fi

losetup -d $DEV0
rm $TMPIMG0
exit $rc
