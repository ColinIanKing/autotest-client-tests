#!/bin/bash
cat << EOF
fix 13212b54d18d5235fb97fbdcba8ae453fd2a3a51

    btrfs: Fix out-of-space bug

    Btrfs will report NO_SPACE when we create and remove files for several times,
    and we can't write to filesystem until mount it again.

    Steps to reproduce:
     1: Create a single-dev btrfs fs with default option
     2: Write a file into it to take up most fs space
     3: Delete above file
     4: Wait about 100s to let chunk removed
     5: goto 2
EOF

TMPIMG=$TMP/test.img
DEV=`losetup -f`

truncate --size 1500m $TMPIMG
losetup $DEV $TMPIMG

# Recommend 1.2G space, too large disk will make test slow

dev_size="$(lsblk -bn -o SIZE "$DEV")" || exit 2
file_size_m=$((dev_size * 75 / 100 / 1024 / 1024))

echo "Loop write ${file_size_m}M file on $((dev_size / 1024 / 1024))M dev"

echo "mkfs $DEV"
mkfs.btrfs -f "$DEV" >/dev/null
if [ $? -ne 0 ]; then
	losetup -d $DEV
	rm -f $TMPIMG
	echo "mkfs.btrfs on $DEV failed"
	exit 1
fi
echo "mount $DEV $MNT"
mount "$DEV" "$MNT"
if [ $? -ne 0 ]; then
	losetup -d $DEV
	rm -f $TMPIMG
	echo "mount $DEV $MNT failed"
	exit 1
fi

for ((loop_i = 0; loop_i < 20; loop_i++)); do
	echo
	echo "loop $loop_i"

	echo "dd file..."
	dd if=/dev/zero of="$MNT"/file0 bs=1M count="$file_size_m"
	ret=$?
	if [ $ret -ne 0 ]; then
		# NO_SPACE error triggered
		echo "dd failed: error: $?"
		umount $DEV
		losetup -d $DEV
		rm -f $TMPIMG
		exit 1
	fi

	echo "rm file..."
	rm -f "$MNT"/file0
	if [ $? -ne 0 ]; then
		umount $DEV
		losetup -d $DEV
		rm -f $TMPIMG
		exit 1
	fi

	for ((i = 0; i < 10; i++)); do
		df "$MNT" | tail -1
		sleep 10
	done
done

umount $DEV
losetup -d $DEV
rm -f $TMPIMG
exit 0
