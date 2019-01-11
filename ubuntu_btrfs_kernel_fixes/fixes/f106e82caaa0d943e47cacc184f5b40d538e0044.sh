#!/bin/bash
cat << EOF
fix f106e82caaa0d943e47cacc184f5b40d538e0044

    Btrfs: Fix a crash when mounting a subvolume

    We should drop dentry before deactivating the superblock, otherwise
    we can hit this bug:

    BUG: Dentry f349a690{i=100,n=/} still in use (1) [unmount of btrfs loop1]
    ...

    Steps to reproduce the bug:

      # mount /dev/loop1 /mnt
      # mkdir save
      # btrfs subvolume snapshot /mnt save/snap1
      # umount /mnt
      # mount -o subvol=save/snap1 /dev/loop1 /mnt
      (crash)

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
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

mkdir $MNT/save
btrfs subvolume snapshot $MNT $MNT/save/snap1
umount $MNT >& /dev/null

mount -o subvol=save/snap1 $DEV0 $MNT >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount -o subvol=$TMP/save/snap1 $DEV0 $MNT failed"
	losetup -d $DEV0
	rm -rf $TMPIMG0 $TMP/save
	exit 1
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit 0
