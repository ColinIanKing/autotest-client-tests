#!/bin/bash
cat << EOF
fix 848cce0d4102b5b4b26b0987b43e1919d462afe2

    Btrfs: avoid setting ->d_op twice

    Follow those instructions, and you'll trigger a warning in the
    beginning of d_set_d_op():

      # mkfs.btrfs /dev/loop3
      # mount /dev/loop3 /mnt
      # btrfs sub create /mnt/sub
      # btrfs sub snap /mnt /mnt/snap
      # touch /mnt/snap/sub
      touch: cannot touch 'tmp': Permission denied

    __d_alloc() set d_op to sb->s_d_op (btrfs_dentry_operations), and
    then simple_lookup() reset it to simple_dentry_operations, which
    triggered the warning.

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

dmesg -c > /dev/null
btrfs sub create $MNT/sub
btrfs sub snap $MNT $MNT/snap
touch $MNT/snap/sub
n=$(dmesg | grep "WARN" | wc -l)
if [ $n -ne 0 ]; then
	echo "Found kernel WARNING"
	dmesg
	umount $MNT >& /dev/null
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi


umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit 0
