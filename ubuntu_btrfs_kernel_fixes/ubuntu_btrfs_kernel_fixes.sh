#!/bin/bash

SCRIPT=$1

clean_loops()
{
	loops=$(grep "loop" /proc/mounts |  awk '{print $1}')
	if [ ! -z "$loops" ]; then
		echo "Found following still mounted: $loops"
		for loop in $loops
		do
			echo "Force unmount of $loop"
			umount $loop
		done
	fi
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

echo "Invoking test $NAME"
echo ""
MNT=$MNT TMP=$TMP FIX=$FIX $SCRIPT
ret=$?

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
