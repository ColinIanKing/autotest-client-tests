#!/bin/bash
cat << EOF
fix 3d84be799194147e04c0e3129ed44a948773b80a

	fix BUG_ON in btrfs_orphan_add() when delete unused block group

EOF

echo "Need large volume!"
exit 0

mntpath=/tmp/btrfs-test
mkdir $mntpath
loopdev=`losetup -f`
filepath=image

umount $mntpath
losetup -d $loopdev
truncate --size 1000g $filepath
losetup $loopdev $filepath
mkfs.btrfs -f $loopdev
mount $loopdev $mntpath

for j in `seq 1 1 1000`; do
	fallocate -l 1g $mntpath/$j
done
# wait cleaner thread remove unused block group
sleep 300

exit 0
