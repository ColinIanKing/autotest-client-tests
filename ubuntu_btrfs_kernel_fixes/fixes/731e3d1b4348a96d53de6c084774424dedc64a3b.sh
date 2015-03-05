#!/bin/bash
cat << EOF
fix 731e3d1b4348a96d53de6c084774424dedc64a3b

    Btrfs: prohibit a operation of changing acl's mask when noacl mount option used

    when used Posix File System Test Suite(pjd-fstest) to test btrfs,
    some cases about setfacl failed when noacl mount option used.
    I simplified used commands in pjd-fstest, and the following steps
    can reproduce it.
    ------------------------
    # cd btrfs-part/
    # mkdir aaa
    # setfacl -m m::rw aaa    <- successed, but not expected by pjd-fstest.
    ------------------------

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

mount $DEV0 $MNT -o noacl >& /dev/null
if [ $? -ne 0 ]; then
	echo "mount $DEV0 $MNT -o noacl failed"
	losetup -d $DEV0
	rm $TMPIMG0
	exit 1
fi

mkdir $MNT/test
setfacl -m m::rw $MNT/test
rc=$?
if [ $rc -eq 0 ]; then
	echo "setfacl succeeded on a noacl mount when it should have failed"
	rc=1
else
	rc=0
fi

umount $MNT >& /dev/null
losetup -d $DEV0
rm $TMPIMG0
exit $rc
