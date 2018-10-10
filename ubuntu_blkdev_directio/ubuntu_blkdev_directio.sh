#!/bin/bash

#
#  Exercise bug fix for LP#1796542
#
BLKDEV_DIO_TEST=$1
LOOPFILE=loop.img
DURATION=30

do_tidy()
{
	losetup -d ${LOOPDEV}
	rm -f ${LOOPFILE}
}

do_trap()
{
	do_tidy
	exit 1
}

if [ $EUID -ne 0 ]; then
	echo "This needs to be run as root"
	exit 1
fi

LOOPDEV=$(losetup -f)

trap "do_tidy" SIGINT SIGTERM SIGHUP

#
# Some system specific info
#
echo "--------------------------------------------------------------------------------"
echo "Date:         " $(date)
echo "Host:         " $(hostname)
echo "Kernel:       " $(uname -rv)
echo "Machine:      " $(uname -npi)
echo "CPUs online:  " $(getconf _NPROCESSORS_ONLN)
echo "CPUs total:   " $(getconf _NPROCESSORS_CONF)
echo "Page size:    " $(getconf PAGE_SIZE)
echo "Pages avail:  " $(getconf _AVPHYS_PAGES)
echo "Pages total:  " $(getconf _PHYS_PAGES)
echo "--------------------------------------------------------------------------------"
echo " "

dd if=/dev/zero of=${LOOPFILE} bs=1M count=64 >& /dev/null

losetup ${LOOPDEV} ${LOOPFILE}
sleep 1

echo "Exercising loop ${LOOPDEV}"

#
#  The BLKDEV_DIO_TEST program will run forever if there
#  is no corruption, or terminate with exit status 1 if
#  it detects a problem.
#
${BLKDEV_DIO_TEST} ${LOOPDEV} 0 &
PID1=$!
${BLKDEV_DIO_TEST} ${LOOPDEV} 2048 &
PID2=$!

N=0
DIED=0
while true
do
	sleep 1
	N=$((N + 1))
	if [ ${N} -gt ${DURATION} ]; then
		break
	fi

	#
	#  Early detection of a terminating child
	#
	if [ ! -d /proc/$PID1 -o  ! -d /proc/$PID2 ]; then
		DIED=1
		break;
	fi
done

kill -9 ${PID1} ${PID2}

#
#  Prematurely exiting processes return 1 too
#
wait $PID1 >& /dev/null
if [ $? -eq 1 ]; then
	DIED=1
fi
wait $PID2 >& /dev/null
if [ $? -eq 1 ]; then
	DIED=1
fi

do_tidy

if [ $DIED -eq 0 ]; then
	echo "PASSED"
	exit 0
else
	echo "FAILED (short pwritev or short pread), see LP#1796542"
	exit 1
fi
