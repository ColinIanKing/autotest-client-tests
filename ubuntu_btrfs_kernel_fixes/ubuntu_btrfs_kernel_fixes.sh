#!/bin/bash

SCRIPT=$1

clean_loops()
{
	loops=$(grep "loop" /proc/mounts | grep -v '/snap/' |  awk '{print $1}')
	if [ ! -z "$loops" ]; then
		echo "Found following still mounted: $loops"
		for loop in $loops
		do
			echo "Force unmount of $loop"
			umount $loop
		done
	fi
}

check_kernel()
{
	n=$(dmesg | grep "Call Trace" | wc -l)
	o=$(dmesg | grep "Oops" | wc -l)
	b=$(dmesg | grep "BUG" | wc -l)
	t=$((n + $o + $b))
	if [ $t -gt 0 ]; then
		echo ""
		echo "Found kernel issue:"
		echo ""
		dmesg
		return 1
	fi
	return 0
}

if [ $EUID -ne 0 ]; then
	echo "$SCRIPT needs to be run as root"
	exit 1
fi

NAME=$(basename $SCRIPT | sed s/.sh//)
MNT=/tmp/mnt-$NAME
TMP=/tmp/tmp-$NAME
TMP=$BINDIR/tmp-$NAME
FIX=$BINDIR/fixes/$NAME

rmdir $MNT $TMP &> /dev/null
mkdir $MNT $TMP

clean_loops

#
# clean kernel log
#
dmesg -c > /dev/null
echo "Invoking test $NAME"
echo "Invoking test $NAME" > /dev/kmsg
echo ""
MNT=$MNT TMP=$TMP FIX=$FIX $SCRIPT
ret=$?
echo "Test $NAME returned $?" > /dev/kmsg

#
# anything bad occurred in the kernel, check after
# 10 seconds as btrfs can trip issues after a few
# seconds because of kthread helpers
#
sleep 10
check_kernel
kern=$?
if [ $kern -ne 0 ]; then
	ret=1
fi

echo ""
if [ $ret -eq 0 ]; then
	echo "PASS: $NAME"
elif [ $ret -eq 1 ]; then
	echo "FAIL: $NAME (ret=$ret)"
elif [ $ret -eq 2 ]; then
	echo "SKIP: $NAME (ret=$ret)"
else
	echo "FAIL: $NAME (ret=$ret)"
fi
echo ""

clean_loops

rmdir $MNT &> /dev/null
rm -rf $TMP
exit $ret
