#!/bin/bash
cat << EOF
fix 8185554d3eb09d23a805456b6fa98dcbb34aa518

    Btrfs: fix incorrect inode acl reset

    When a directory has a default ACL and a subdirectory is created
    under that directory, btrfs_init_acl() is called when the
    subdirectory's inode is created to initialize the inode's ACL
    (inherited from the parent directory) but it was clearing the ACL
    from the inode after setting it if posix_acl_create() returned
    success, instead of clearing it only if it returned an error.

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

mkdir $MNT/acl
setfacl -d --set u::rwx,g::rwx,o::- $MNT/acl
getfacl $MNT/acl

mkdir $MNT/acl/dir1
getfacl $MNT/acl/dir1

umount $MNT
mount $DEV0 $MNT
getfacl $MNT/acl/dir1

getfacl $MNT/acl/dir1 | grep -v "#" | grep -e '^$' -v | sort > $TMP/getfacl.new
sort > $TMP/getfacl.ok << EOD
user::rwx
group::rwx
other::---
default:user::rwx
default:group::rwx
default:other::---
EOD

diff $TMP/getfacl.ok $TMP/getfacl.new
if [ $? -ne 0 ]; then
	echo "Unexpected getfacl output"
	rc=1
else
	rc=0
fi

rm -f $TMP/getfacl.ok $TMP/getfacl.new

umount $MNT >& /dev/null
losetup -d $DEV0
rm -f $TMPIMG0
exit $rc
