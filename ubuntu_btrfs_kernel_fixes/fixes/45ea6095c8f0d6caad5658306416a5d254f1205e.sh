#!/bin/bash
cat << EOF
fix 45ea6095c8f0d6caad5658306416a5d254f1205e

    btrfs: fix double-free 'tree_root' in 'btrfs_mount()'

    On error path 'tree_root' is treed in 'free_fs_info()'.
    No need to free it explicitely. Noticed by SLUB in debug mode:

    Complete reproducer under usermode linux (discovered on real
    machine):

        bdev=/dev/ubda
        btr_root=/btr
        /mkfs.btrfs $bdev
        mount $bdev $btr_root
        mkdir $btr_root/subvols/
        cd $btr_root/subvols/
        /btrfs su cr foo
        /btrfs su cr bar
        mount $bdev -osubvol=subvols/foo $btr_root/subvols/bar
        umount $btr_root/subvols/bar

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
mkdir $MNT/subvols/
cd $MNT/subvols/
btrfs su cr foo
btrfs su cr bar
mount $DEV0 -osubvol=subvols/foo $MNT/subvols/bar
umount $MNT/subvols/bar

cd - >& /dev/null
rc=0
n=$(dmesg | grep BUG | wc -l)
if [ $n -gt 0 ]; then
	"echo found kernel BUG"
	dmesg
	rc=1
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
