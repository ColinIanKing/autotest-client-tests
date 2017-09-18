#!/bin/bash
#
# Copyright (C) 2017 Canonical
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#

#
#  Trival "smoke test" sysdig tests just to see
#  if basic functionality works
#
TMPFILE=${PWD}sysdig-kernel-trace-$$.tmp
#
#  Number of blocks in sysdig trace file
#  For non-POSIX mode, this is 1K blocks
#
BLK_LIMIT=16384

passed=0
failed=0

#
#  Number of sysdig trace attempts before giving up
#
TRIES=10
#
#  Minimal number of events to capture
#
THRESHOLD=25

#
#  Minimal time to run dd for in seconds
#
DURATION=4

inc_failed()
{
	failed=$((failed + 1))
}

check()
{
	if [ $1 -ge ${THRESHOLD} ]; then
		echo "PASSED ($2)"
		passed=$((passed + 1))
		return 0
	fi

	echo "FAILED ($2)"
	inc_failed
	rc=1
	return 1
}

test_sysdig_context_switch()
{
	echo "== sysdig smoke test to trace dd, cat, read and writes =="

	echo "Limiting raw capture file to ${BLK_LIMIT} blocks"

	#
	#  We try this several times as we may not capture enough events
	#  first time around
	#
	for i in $(seq ${TRIES})
	do
		dmesg -c > /dev/null
		echo "Try $i of ${TRIES}"
		ulimit -Sf ${BLK_LIMIT}
		sysdig --unbuffered -w ${TMPFILE}.raw >& /dev/null &
		pid=$!

		count=0
		while true
		do
			n=$(dmesg | grep "starting capture" | wc -l)
			if [ $n -gt 0 ]; then
				echo "Sysdig capture started after $count seconds wait"
				break
			fi
			sleep 1
			count=$((count + 1))
			if [ $count -gt 45 ]; then
				echo "Could not find start of capture message, maybe sysdig didn't start?"
				break
			fi
		done
		start=$(date +%s)
		#
		#  Capture at least $DURATION sections of events
		#
		while true
		do
			(dd if=/dev/zero bs=1024 count=500000 | cat | cat | dd bs=1024 of=/dev/null) >& /dev/null
			end=$(date +%s)
			duration=$((end - $start))
			if [ $duration -ge ${DURATION} ]; then
				break
			fi
			#
			#  Has sysdig terminated?
			#
			if [ ! -d /proc/$pid ]; then
				break;
			fi
		done

		#
		#  restore file limit
		#
		ulimit -f hard

		#
		#  Timed out? then kill sysdig
		#
		if [ -d  /proc/$pid ]; then
			kill -SIGINT $pid
			sleep 1
			kill -SIGKILL $pid
			wait $pid
		fi

		sz=$(stat -c%s ${TMPFILE}.raw)
		echo "Raw capture file is $((sz / 1048576)) Mbytes"
		(sysdig -r ${TMPFILE}.raw > ${TMPFILE}) >& /dev/null
		sz=$(stat -c%s ${TMPFILE})
		echo "Converted events file is $((sz / 1048576)) Mbytes"

		events=$(wc -l ${TMPFILE} | cut -d' ' -f1)
		switches_dd=$(grep switch ${TMPFILE} | grep dd | wc -l | cut -d' ' -f1)
		switches_cat=$(grep switch ${TMPFILE} | grep cat | wc -l | cut -d' ' -f1)
		ddrdzero=$(grep dd ${TMPFILE} | grep read | grep "/dev/zero" | wc -l | cut -d' ' -f1)
		ddwrnull=$(grep dd ${TMPFILE} | grep write | grep "/dev/null" | wc -l | cut -d' ' -f1)

		if [ $switches_dd -ge ${THRESHOLD} -a \
		     $switches_cat -ge ${THRESHOLD} -a \
		     $ddrdzero -ge ${THRESHOLD} -a \
		     $ddwrnull -ge ${THRESHOLD} ]; then
			break
		fi
		rm -f ${TMPFILE}.raw ${TMPFILE}
	done

	echo "Found:"
	echo "   ${events} sysdig events"
	echo "   ${switches_dd} dd context switches"
	echo "   ${switches_cat} cat context switches"
	echo "   ${ddrdzero} reads from /dev/zero by dd"
	echo "   ${ddwrnull} writes to /dev/null by dd"

	check ${switches_dd} "trace at least ${THRESHOLD} context switches involving dd"
	check ${switches_cat} "trace at least ${THRESHOLD} context switches involving cat"
	check ${ddrdzero} "trace at least ${THRESHOLD} reads of /dev/zero by dd"
	check ${ddwrnull} "trace at least ${THRESHOLD} writes to /dev/null by dd"
}

rc=0
test_sysdig_context_switch
echo " "

rm -rf ${TMPFILE}

echo "Summary: ${passed} passed, ${failed} failed"

exit ${rc}
