#!/bin/bash
cat << EOF
fix 800ee2247f483b6d05ed47ef3bbc90b56451746c

   btrfs: fix crash in remount(thread_pool=) case

    Reproducer:
        mount /dev/ubda /mnt
        mount -oremount,thread_pool=42 /mnt

    Gives a crash:
        ? btrfs_workqueue_set_max+0x0/0x70
        btrfs_resize_thread_pool+0xe3/0xf0
        ? sync_filesystem+0x0/0xc0
        ? btrfs_resize_thread_pool+0x0/0xf0
        btrfs_remount+0x1d2/0x570
        ? kern_path+0x0/0x80
        do_remount_sb+0xd9/0x1c0
        do_mount+0x26a/0xbf0
        ? kfree+0x0/0x1b0
        SyS_mount+0xc4/0x110

    It's a call
        btrfs_workqueue_set_max(fs_info->scrub_wr_completion_workers, new_pool_size);
    with
        fs_info->scrub_wr_completion_workers = NULL;

    as scrub wqs get created only on user's demand.

EOF

TMPIMG=$TMP/test.img
DEV=/dev/loop0

truncate --size 256M $TMPIMG
losetup $DEV $TMPIMG

mkfs.btrfs -f $DEV >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs on $DEV failed"
	losetup -d $DEV
	rm -f $TMPIMG
	exit 1
fi

for i in $(seq 20)
do
	mount $DEV $MNT
	if [ $? -ne 0 ]; then
		echo "mount $DEV $MNT failed"
		losetup -d $DEV
		rm -f $TMPIMG
		exit 1
	fi

	mount -oremount,thread_pool=42 $MNT
	if [ $? -ne 0 ]; then
		echo "mount -oremount,thread_pool=42 /mnt failed"
		umount $DEV
		losetup -d $DEV
		rm -f $TMPIMG
		exit 1
	fi
	umount $DEV
done

losetup -d $DEV
rm -f $TMPIMG
exit 0
