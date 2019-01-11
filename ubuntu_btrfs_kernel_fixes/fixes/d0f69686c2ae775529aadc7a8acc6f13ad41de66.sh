#!/bin/bash
cat << EOF
fix d0f69686c2ae775529aadc7a8acc6f13ad41de66

    Btrfs: Don't return acl info when mounting with noacl option

    Steps to reproduce:

      # mkfs.btrfs /dev/sda2
      # mount /dev/sda2 /mnt
      # touch /mnt/file0
      # setfacl -m 'u:root:x,g::x,o::x' /mnt/file0
      # umount /mnt
      # mount /dev/sda2 -o noacl /mnt
      # getfacl /mnt/file0
      ...
      user::rw-
      user:root:--x
      group::--x
      mask::--x
      other::--x

    The output should be:

      user::rw-
      group::--x
      other::--x

EOF

TMPIMG0=$TMP/test0.img

DEV0=`losetup -f`

truncate --size 256M $TMPIMG0

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

touch $MNT/file0
setfacl -m 'u:root:x,g::x,o::x' $MNT/file0
umount $MNT

mount -o noacl $DEV0 $MNT

echo "getfacl $MNT/file0 returns:"
getfacl $MNT/file0
echo ""

getfacl $MNT/file0 | grep -v "#" | grep -e '^$' -v | sort > $TMP/getfacl.new

sort > $TMP/getfacl.ok << EOD
user::rw-
group::--x
other::--x
EOD

diff $TMP/getfacl.ok $TMP/getfacl.new
if [ $? -ne 0 ]; then
	echo "Unexpected getfacl output, noacl mount option issue"
	rc=1
else
	rc=0
fi

rm -f $TMP/getfacl.ok $TMP/getfacl.new

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
