#!/bin/bash
cat << EOF
fix 306424cc880a0fbbdc99eee1f43d056a301a180f

    Btrfs: fix ctime update of on-disk inode

    To reproduce the bug:

        # touch /mnt/tmp
        # stat /mnt/tmp | grep Change
        Change: 2011-12-09 09:32:23.412105981 +0800
        # chattr +i /mnt/tmp
        # stat /mnt/tmp | grep Change
        Change: 2011-12-09 09:32:43.198105295 +0800
        # umount /mnt
        # mount /dev/loop1 /mnt
        # stat /mnt/tmp | grep Change
        Change: 2011-12-09 09:32:23.412105981 +0800

    We should update ctime of in-memory inode before calling
    btrfs_update_inode().

EOF

TMPIMG0=$TMP/test0.img
DEV0=/dev/loop0

truncate --size 256M $TMPIMG0
losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs $DEV0 failed"
	losetup -d $DEV0
	rm $TMPIMG0
	exit 1
fi

mount $DEV0 $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT failed"
	losetup -d $DEV0
	rm $TMPIMG0
	exit 1
fi

rc=0

touch $MNT/tmp
stat $MNT/tmp | grep Change
sleep 1

chattr +i $MNT/tmp
stat $MNT/tmp | grep Change
t1=$(stat $MNT/tmp | grep Change | awk '{ print $3 }')
sleep 1

umount $MNT
mount $DEV0 $MNT >& /dev/null
stat $MNT/tmp | grep Change
t2=$(stat $MNT/tmp | grep Change | awk '{ print $3 }')

if [ $t1 == $t2 ]; then
	rc=0
else
	echo "Got different time stamps: $t1 vs $t2"
	rc=1
fi
umount $MNT >& /dev/null
losetup -d $DEV0
rm $TMPIMG0
exit $rc
