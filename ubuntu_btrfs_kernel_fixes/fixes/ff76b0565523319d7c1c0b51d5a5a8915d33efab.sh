#!/bin/bash
cat << EOF
fix ff76b0565523319d7c1c0b51d5a5a8915d33efab

    Btrfs: Don't allocate inode that is already in use

    Due to an off-by-one error, it is possible to reproduce a bug
    when the inode cache is used.

    The same inode number is assigned twice, the second time this
    leads to an EEXIST in btrfs_insert_empty_items().

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

mount $DEV0 $MNT -o rw,relatime,compress=lzo,space_cache,inode_cache >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT -o rw,relatime,compress=lzo,space_cache,inode_cache failed"
	losetup -d $DEV0
	rm $TMPIMG0
	exit 1
fi

btrfs subv create $MNT/s1
for i in `seq 34027`
do
	touch $MNT/s1/${i}
done
btrfs subv snap $MNT/s1 $MNT/s2


dmesg -c > /dev/null
FILENAME=$(find $MNT/s1/ -inum 4085 | sed 's|^.*/\([^/]*\)$|\1|')

rm $MNT/s2/$FILENAME
touch $MNT/s2/$FILENAME
# the following steps can be repeated to reproduce the issue again and again
[ -e $MNT/s3 ] && btrfs subv del $MNT/s3
[ -e $TMP/failed ] && rm $TMP/failed
btrfs subv snap $MNT/s2 $MNT/s3
rm $MNT/s3/$FILENAME
for i in `seq 3 34027`
do
	touch $MNT/s3/__${i} || touch $TMP/failed
done

rc=0
if [ -e $TMP/failed ]; then
	echo "allocated an inode that already exxists"
	rc=1
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm $TMPIMG0
exit $rc
