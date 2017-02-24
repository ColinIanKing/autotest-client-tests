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
TMPFILE=/tmp/sysdig-kernel-trace-$$.tmp

passed=0
failed=0

THRESHOLD=500

inc_failed()
{
	failed=$((failed + 1))
}

check()
{
	if [ $1 -gt $THRESHOLD ]; then
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

	sysdig --unbuffered -w ${TMPFILE}.raw &
	pid=$!
	(dd if=/dev/zero bs=1024 count=250000 | cat | cat | dd bs=1024 of=/dev/null) >& /dev/null
	kill -SIGINT $pid
	wait $pid

	echo "Converting raw events to human readable format.."
	sysdig -r ${TMPFILE}.raw > ${TMPFILE}


	echo "Found:"
	events=$(wc -l ${TMPFILE} | cut -d' ' -f1)
	echo "   $events sysdig events"
	switches_dd=$(grep switch ${TMPFILE} | grep dd | wc -l | cut -d' ' -f1)
	echo "   $switches_dd dd context switches"
	switches_cat=$(grep switch ${TMPFILE} | grep cat | wc -l | cut -d' ' -f1)
	echo "   $switches_cat cat context switches"
	ddrdzero=$(grep dd ${TMPFILE} | grep read | grep "/dev/zero" | wc -l | cut -d' ' -f1)
	echo "   $ddrdzero reads from /dev/zero by dd"
	ddwrnull=$(grep dd ${TMPFILE} | grep write | grep "/dev/null" | wc -l | cut -d' ' -f1)
	echo "   $ddwrnull writes to /dev/null by dd"

	check $switches_dd "trace at least $THRESHOLD context switches involving dd"
	check $switches_cat "trace at least $THRESHOLD context switches involving cat"
	check $ddrdzero "trace at least $THRESHOLD reads of /dev/zero by dd"
	check $ddwrnull "trace at least $THRESHOLD writes to /dev/null by dd"

	rm -f ${TMPFILE} ${TMPFILE}.raw
}

rc=0
test_sysdig_context_switch
echo " "

rm -rf $TMPFILE

echo "Summary: $passed passed, $failed failed"

exit $rc
