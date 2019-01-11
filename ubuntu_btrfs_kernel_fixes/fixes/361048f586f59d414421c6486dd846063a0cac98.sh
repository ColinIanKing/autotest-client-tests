#!/bin/bash
cat << EOF
fix 361048f586f59d414421c6486dd846063a0cac98

    Btrfs: fix full backref problem when inserting shared block reference
    
    If we create several snapshots at the same time, the following BUG_ON() will be
    triggered.
    
        kernel BUG at fs/btrfs/extent-tree.c:6047!

    Steps to reproduce:
     # mkfs.btrfs <partition>
     # mount <partition> <mnt>
     # cd <mnt>
     # for ((i=0;i<2400;i++)); do touch long_name_to_make_tree_more_deep$i; done
     # for ((i=0; i<4; i++))
     > do
     > mkdir $i
     > for ((j=0; j<200; j++))
     > do
     > btrfs sub snap . $i/$j
     > done &
     > done

EOF

TMPIMG0=$TMP/test0.img

DEV0=`losetup -f`

truncate --size 512M $TMPIMG0

losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0  >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs -f $DEV0 failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

mount $DEV0 $MNT
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT failed"
	losetup -d $DEV0
	rm -f $TMPIMG0
	exit 1
fi

cd $MNT

dmesg -c > /dev/null

for ((i=0;i<2400;i++))
do
	touch long_name_to_make_tree_more_deep$i
done

for ((i=0; i<4; i++))
do
	mkdir $i
	for ((j=0; j<200; j++))
	do
		btrfs sub snap . $i/$j >& /dev/null
	done &
done

cd - >& /dev/null

for ((j=0; j<200; j++))
do
	wait
done

rc=0
n=$(dmesg | grep "BUG" | wc -l)
if [ $n -gt 0 ]; then
	rc=1
	echo "Found kernel BUG"
	dmesg
fi

umount $MNT
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
