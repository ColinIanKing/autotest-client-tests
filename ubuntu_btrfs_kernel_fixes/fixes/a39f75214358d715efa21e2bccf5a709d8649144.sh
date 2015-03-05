#!/bin/bash
cat << EOF
fix a39f75214358d715efa21e2bccf5a709d8649144

    Btrfs: fix wrong nbytes information of the inode

    If we write some data into the data hole of the file(no preallocation for this
    hole), Btrfs will allocate some disk space, and update nbytes of the inode, but
    the other element--disk_i_size needn't be updated. At this condition, we must
    update inode metadata though disk_i_size is not changed(btrfs_ordered_update_i_size()
    return 1).

     # mkfs.btrfs /dev/sdb1
     # mount /dev/sdb1 /mnt
     # touch /mnt/a
     # truncate -s 856002 /mnt/a
     # dd if=/dev/zero of=/mnt/a bs=4K count=1 conv=nocreat,notrunc
     # umount /mnt
     # btrfsck /dev/sdb1
     root 5 inode 257 errors 400
     found 32768 bytes used err is 1

EOF

TMPIMG0=$TMP/test0.img

DEV0=/dev/loop0

truncate --size 512M $TMPIMG0

losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 failed"
	losetup -d $DEV0
	rm $TMPIMG0
	exit 1
fi

mount $DEV0 $MNT >& /dev/null

touch $MNT/a
dd if=/dev/zero of=$MNT/a seek=8 count=1 bs=4K oflag=direct conv=nocreat,notrunc >& /dev/null
umount $MNT >& /dev/null

#
#  There should be no errors if the file extent is correct
#
n=$(btrfsck $DEV0 | grep "err is 1" | wc -l)
if [ $n -ne -0 ]; then
	echo "btrfsck found some unexpected errors"
	losetup -d $DEV0
	rm $TMPIMG0
	exit 1
fi

losetup -d $DEV0
rm $TMPIMG0
exit 0
