#!/bin/bash
cat << EOF
fix c9a9dbf2cbd1641af49bf081ca3bbe4101df3991

    Btrfs: fix a warning when disabling quota

    Obviously, this warn_on() is unnecessary, and it will be easily triggered.
    Just remove it.

EOF

TMPIMG0=$TMP/test0.img
DEV0=`losetup -f`

truncate --size 512M $TMPIMG0
losetup $DEV0 $TMPIMG0

mkfs.btrfs -f $DEV0 >& /dev/null
if [ $? -ne 0 ]; then
	echo "mkfs.btrfs $DEV0 failed"
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

btrfs quota enable $MNT
btrfs sub create $MNT/subv
btrfs qgroup limit 10M $MNT/subv

dmesg -c > /dev/null
i=1
while [ $i -le 10000 ]
do
	dd if=/dev/zero of=$MNT/subv/data_$i bs=1K count=1 >& /dev/null
	i=$(($i+1))
	if [ $i -eq 500 ]
	then
		btrfs quota disable $MNT
	fi
done
n=$(dmesg | grep WARN | wc -l)
if [ $n -ne 0 ]; then
	echo "Found kernel WARN messages"
	dmesg
	rc=1
else
	rc=0
fi

umount $DEV0
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
