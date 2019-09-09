#!/bin/bash

if [ $# -ne 2 ]; then
	echo "Need to pass test number into script and srcpath"
	exit 1
fi
TEST=$1
VDEV_PATH=$2

POOL=testpool
TESTDIR=test
SCRATCHDIR=scratch

export TEST_DIR=/mnt/$TESTDIR
export TEST_DEV=$POOL/$TESTDIR
export SCRATCH_MNT=/mnt/$SCRATCHDIR
export SCRATCH_DEV=$POOL/$SCRATCHDIR
export FSTYP=zfs

vdev0=${VDEV_PATH}/block-dev-0
vdev1=${VDEV_PATH}/block-dev-1
vdev2=${VDEV_PATH}/block-dev-2
vdev3=${VDEV_PATH}/block-dev-3
vdev4=${VDEV_PATH}/block-dev-4

truncate -s 1G ${vdev0}
truncate -s 1G ${vdev1}
truncate -s 1G ${vdev2}
truncate -s 1G ${vdev3}
truncate -s 1G ${vdev4}

echo "Creating zfs pool $POOL.."
zpool create $POOL mirror $vdev0 $vdev1 -f
zpool add $POOL mirror $vdev2 $vdev3 -f
zpool add $POOL log $vdev4 -f
echo "Creating zfs file systems $TESTDIR and $SCRATCHDIR in $POOL.."
zfs create $POOL/$TESTDIR
zfs create $POOL/$SCRATCHDIR
zfs set acltype=posixacl $POOL/$TESTDIR
zfs set acltype=posixacl $POOL/$SCRATCHDIR
zfs set compression=on $POOL/$TESTDIR
#zfs set copies=3 $POOL/$TESTDIR
#zfs set dedup=on $POOL/$TESTDIR
zfs set mountpoint=legacy $POOL/$TESTDIR
zfs set mountpoint=legacy $POOL/$SCRATCHDIR


echo "VDEVs in ${VDEV_PATH}"
mkdir /mnt/$TESTDIR /mnt/$SCRATCHDIR
./check -zfs "generic/$TEST"
rc=$?
rmdir /mnt/$TESTDIR /mnt/$SCRATCHDIR

#zfs umount $POOL
echo "Destroying zfs pool $POOL"
zpool destroy $POOL
echo "Removing VDEVs in ${VDEV_PATH}"
dd if=/dev/zero if=${vdev0} bs=1M count=1024 >& /dev/null
rm -rf $vdev0
dd if=/dev/zero if=${vdev1} bs=1M count=1024 >& /dev/null
rm -rf $vdev1
dd if=/dev/zero if=${vdev2} bs=1M count=1024 >& /dev/null
rm -rf $vdev2
dd if=/dev/zero if=${vdev3} bs=1M count=1024 >& /dev/null
rm -rf $vdev3
dd if=/dev/zero if=${vdev4} bs=1M count=1024 >& /dev/null
rm -rf $vdev4

exit $rc
