#!/bin/bash
cat << EOF
fix 0e78340f3c1fc603e8016c8ac304766bcc65506e

    Btrfs: fix error handling in btrfs_get_sb

    If we failed to find the root subvol id, or the subvol=<name>, we would
    deactivate the locked super and close the devices.  The problem is at this point
    we have gotten the SB all setup, which includes setting super_operations, so
    when we'd deactiveate the super, we'd do a close_ctree() which closes the
    devices, so we'd end up closing the devices twice.  So if you do something like
    this

    mount /dev/sda1 /mnt/test1
    mount /dev/sda1 /mnt/test2 -o subvol=xxx
    umount /mnt/test1

    it would blow up (if subvol xxx doesn't exist).  This patch fixes that problem.

EOF

TMPIMG0=$TMP/test0.img

DEV0=/dev/loop0

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
mount $DEV0 $MNT -o subvol=xxx >& /dev/null
if [ $? -eq 0 ]; then
	echo "mount $DEV0 $MNT -o subvol=xxx succeeded and it was expected to fail"
	umount $MNT >& /dev/null
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit 0
