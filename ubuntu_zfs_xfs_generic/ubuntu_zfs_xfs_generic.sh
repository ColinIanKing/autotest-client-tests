#!/bin/bash

if [ $# -ne 1 ]; then
	echo "Need to pass test number into script"
	exit 1
fi
TEST=$1

POOL=testpool
TESTDIR=test
SCRATCHDIR=scratch

export TEST_DIR=/mnt/$TESTDIR
export TEST_DEV=$POOL/$TESTDIR
export SCRATCH_MNT=/mnt/$SCRATCHDIR
export SCRATCH_DEV=$POOL/$SCRATCHDIR
export FSTYP=zfs

truncate -s 1G block-dev-0
truncate -s 1G block-dev-1
truncate -s 1G block-dev-2
truncate -s 1G block-dev-3
truncate -s 1G block-dev-4
truncate -s 1G block-dev-5

dev0=$(losetup --find --show block-dev-0)
dev1=$(losetup --find --show block-dev-1)
dev2=$(losetup --find --show block-dev-2)
dev3=$(losetup --find --show block-dev-3)
dev4=$(losetup --find --show block-dev-4)
dev5=$(losetup --find --show block-dev-5)

echo "Creating zfs pool $POOL.."
zpool create $POOL mirror $dev0 $dev1 -f
zpool add $POOL mirror $dev2 $dev3 -f
zpool add $POOL log $dev4 -f
zpool add $POOL cache $dev5 -f
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
losetup -d $dev0 $dev1 $dev2 $dev3 $dev4 $dev5
rm block-dev-0 block-dev-1 block-dev-2 block-dev-3 block-dev-4 block-dev-5

exit $rc
