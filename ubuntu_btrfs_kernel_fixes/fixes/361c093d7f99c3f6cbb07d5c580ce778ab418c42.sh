#!/bin/bash
cat << EOF
fix 361c093d7f99c3f6cbb07d5c580ce778ab418c42

    Btrfs: Wait for uuid-tree rebuild task on remount read-only

    If the user remounts the filesystem read-only while the uuid-tree
    scan and rebuild task is still running (this happens once after the
    filesystem was mounted with an old kernel, or when forced with the
    mount options), the remount should wait on the tasks completion
    before setting the filesystem read-only. Otherwise the background
    task continues to write to the filesystem which is apparently not
    what users expect.

EOF

TMPIMG0=$TMP/test0.img

DEV0=/dev/loop0

truncate --size 2G $TMPIMG0
losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 failed"
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

for i in $(seq 50000)
do
	btrfs subvolume create ${MNT}/$i >& /dev/null
done

umount $MNT
mount $DEV0 $MNT -o rescan_uuid_tree >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT -o rescan_uuid_tree failed"
	losetup -d $DEV0
	rm $TMPIMG0
	exit 1
fi
sleep 1
n1=$(ps -elf | fgrep '[btrfs-uuid]' | grep -v grep | wc -l)
mount $TEST_DEV $MNT -o ro,remount
n2=$(ps -elf | fgrep '[btrfs-uuid]' | grep -v grep | wc -l)
sleep 1
rc=0
if [ $n2 -gt 0 ]; then
	echo "failed:  remount did not wait on the rebuild task completion"
	rc=1
fi

umount $DEV0 >& /dev/null
losetup -d $DEV0
rm $TMPIMG0
exit $rc
