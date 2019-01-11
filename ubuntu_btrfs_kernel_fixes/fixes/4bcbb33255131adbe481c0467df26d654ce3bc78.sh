#!/bin/bash
cat << EOF
fix 4bcbb33255131adbe481c0467df26d654ce3bc78

    Btrfs: fix incorrect compression ratio detection

    Steps to reproduce:
     # mkfs.btrfs -f /dev/sdb
     # mount -t btrfs /dev/sdb /mnt -o compress=lzo
     # dd if=/dev/zero of=/mnt/data bs=$((33*4096)) count=1

    after previous steps, inode will be detected as bad compression ratio,
    and NOCOMPRESS flag will be set for that inode.

    Reason is that compress have a max limit pages every time(128K), if a
    132k write in, it will be splitted into two write(128k+4k), this bug
    is a leftover for commit 68bb462d42a(Btrfs: don't compress for a small write)

    Fix this problem by checking every time before compression, if it is a
    small write(<=blocksize), we bail out and fall into nocompression directly.
EOF

TMPIMG=$TMP/test.img
DEV=`losetup -f`

truncate --size 256M $TMPIMG
losetup $DEV $TMPIMG

mkfs.btrfs -f "$DEV" >& /dev/null
if [ $? -ne 0 ]; then
	losetup -d $DEV
	rm -f $TMPIMG
	echo "mkfs.btrfs on $DEV failed"
	exit 1
fi
mount "$DEV" "$MNT" -o compress=lzo
if [ $? -ne 0 ]; then
	losetup -d $DEV
	rm -f $TMPIMG
	echo "mount $DEV $MNT failed"
	exit 1
fi

n1=$(du -B 1 $MNT | awk '{print $1}')
dd if=/dev/zero of=$MNT/data bs=$((33*4096)) count=1 >& /dev/null
n2=$(du -B 1 $MNT | awk '{print $1}')
bytes=$((n2 - n1))

echo "Size is $bytes, expecting size less than 135168 bytes"
rc=0
if [ $bytes -ge 135168 ]; then
	rc=1
fi

umount $DEV
losetup -d $DEV
rm -f $TMPIMG
exit $rc
