#!/bin/bash
cat << EOF
fix 7b119a8b8998f17abd6caf928dee5bf203eef8c5

    Btrfs: fix incremental send's decision to delay a dir move/rename

    It's possible to change the parent/child relationship between directories
    in such a way that if a child directory has a higher inode number than
    its parent, it doesn't necessarily means the child rename/move operation
    can be performed immediately. The parent migth have its own rename/move
    operation delayed, therefore in this case the child needs to have its
    rename/move operation delayed too, and be performed after its new parent's
    rename/move.

EOF

TMPIMG0=$TMP/test0.img
DEV0=/dev/loop0

truncate --size 1G $TMPIMG0
losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0
mount $DEV0 $MNT

umount $MNT
mkfs.btrfs -f $DEV0
mount $DEV0 $MNT

mkdir $MNT/A
mkdir $MNT/B
mkdir $MNT/C
mv $MNT/C $MNT/A
mv $MNT/B $MNT/A/C
mkdir $MNT/A/C/D

btrfs subvolume snapshot -r $MNT $MNT/snap1
btrfs send $MNT/snap1 -f $TMP/base.send

mv $MNT/A/C/D $MNT/A/D2
mv $MNT/A/C/B $MNT/A/D2/B2
mv $MNT/A/C $MNT/A/D2/B2/C2

btrfs subvolume snapshot -r $MNT $MNT/snap2
btrfs send -p $MNT/snap1 $MNT/snap2 -f $TMP/incremental.send

rc=$?
if [ $rc -ne 0 ]; then
	echo "incremental send failed"
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm $TMPIMG0
exit $rc
