#!/bin/bash

if [ $# -ne 1 ]; then
	echo "Need to pass test number into script"
	exit 1
fi
TEST=$1

POOL=testpool
TESTDIR=test
SCRATCHDIR=scratch
MYPWD=$(pwd)

export TEST_DIR=/mnt/$TESTDIR
export TEST_DEV=$POOL/$TESTDIR
export SCRATCH_MNT=/mnt/$SCRATCHDIR
export SCRATCH_DEV=$POOL/$SCRATCHDIR
export FSTYP=zfs

vdev0=${MYPWD}/block-dev-0
vdev1=${MYPWD}/block-dev-1
vdev2=${MYPWD}/block-dev-2
vdev3=${MYPWD}/block-dev-3
vdev4=${MYPWD}/block-dev-4

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
zfs set copies=3 $POOL/$TESTDIR
zfs set dedup=on $POOL/$TESTDIR
zfs set mountpoint=legacy $POOL/$TESTDIR
zfs set mountpoint=legacy $POOL/$SCRATCHDIR

zfs umount $POOL

mkdir /mnt/$TESTDIR /mnt/$SCRATCHDIR
./check -zfs "generic/$TEST"
rc=$?
rmdir /mnt/$TESTDIR /mnt/$SCRATCHDIR

echo "Destroying zfs pool $POOL"
zpool destroy $POOL
rm -rf $vdev0 $vdev1 $vdev2 $vdev3 $vdev4

exit $rc
