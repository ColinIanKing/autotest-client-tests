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
#  Trival "smoke test" lttng tests just to see
#  if basic functionality works
#
SESSION=/tmp/lttng-kernel-trace-$$-session
SESSION_NAME=test-kernel-session
TMPFILE=/tmp/lttng-kernel-trace-$$.tmp

passed=0
failed=0

inc_failed()
{
	failed=$((failed + 1))
}

check()
{
	if [ $1 -eq 0 ]; then
		echo "PASSED ($2)"
		passed=$((passed + 1))
		return 0
	fi

	echo "FAILED ($2)"
	inc_failed
	rc=1
	return 1
}

test_lttng_session_create()
{
	echo "== lttng smoke test of session create/destroy =="
	lttng create ${SESSION_NAME} --output=${SESSION}
	check $? "lttng create"
	lttng destroy
	check $? "lttng destroy"
}

test_lttng_list_kernel()
{
	echo "== lttng smoke test list kernel events =="
	lttng list --kernel > $TMPFILE
	check $? "lttng list --kernel"
	n=$(wc -l < $TMPFILE | cut -d' ' -f1)
	if [ $n -lt 3 ]; then
		echo "FAILED (lttng list --kernel more output expected)"
	fi
	rm -f $TMPFILE
}

test_lttng_list_kernel_syscall()
{
	lttng list --kernel --syscall > $TMPFILE
	check $? "lttng list --kernel --syscall"
	n=$(wc -l < $TMPFILE | cut -d' ' -f1)
	if [ $n -lt 3 ]; then
		echo "FAILED (lttng list --kernel --syscall more output expected)"
	fi
	rm -f $TMPFILE
}

test_lttng_open_close()
{
	echo "== lttng smoke test trace open/close system calls =="
	lttng create ${SESSION_NAME} --output=${SESSION}
	check $? "lttng create"
	if [ $? -ne 0 ]; then
		return 1
	fi

	lttng enable-event --kernel --syscall open,openat,close
	check $? "lttng enable-event"
	if [ $? -ne 0 ]; then
		lttng destroy
		return 1
	fi

	lttng start
	check $? "lttng start"
	if [ $? -ne 0 ]; then
		lttng destroy
		return 1
	fi

	cat /proc/cpuinfo > /dev/null

	lttng stop
	check $? "lttng stop"
	if [ $? -ne 0 ]; then
		lttng destroy
		return 1
	fi

	lttng destroy
	check $? "lttng destroy"
	if [ $? -ne 0 ]; then
		return 1
	fi

	babeltrace ${SESSION}* > $TMPFILE
	opens=$(grep open $TMPFILE | wc -l | cut -d' ' -f1)
	closes=$(grep close $TMPFILE | wc -l | cut -d' ' -f1)
	procs=$(grep "/proc/cpuinfo" $TMPFILE | wc -l | cut -d' ' -f1)

	if [ $opens -lt 1 ]; then
		inc_failed
		echo "FAILED (did not trace any open system calls)"
		rc=1
		return 1
	fi
	if [ $closes -lt 1 ]; then
		inc_failed
		echo "FAILED (did not trace any close system calls)"
		rc=1
		return 1
	fi
	if [ $procs -lt 1 ]; then
		inc_failed
		echo "FAILED (did not trace open on /proc/cpuinfo)"
		rc=1
		return 1
	fi
	echo "PASSED (simple system call tracing with babeltrace)"
	return 0
}

test_lttng_context_switch()
{
	echo "== lttng smoke test trace context switches =="
	lttng create ${SESSION_NAME} --output=${SESSION}
	check $? "lttng create"
	if [ $? -ne 0 ]; then
		inc_failed
		return 1
	fi

	lttng enable-event --kernel sched_switch
	check $? "lttng enable-event"
	if [ $? -ne 0 ]; then
		inc_failed
		lttng destroy
		return 1
	fi

	lttng start
	check $? "lttng start"
	if [ $? -ne 0 ]; then
		inc_failed
		lttng destroy
		return 1
	fi

	sleep 2
	(dd if=/dev/zero bs=4096 count=100000 | cat | cat | cat | dd bs=4096 > /dev/null) >& /dev/null
	(dd if=/dev/zero bs=4096 count=100000 | cat | cat | cat | dd bs=4096 > /dev/null) >& /dev/null
	sleep 2

	lttng stop
	check $? "lttng stop"
	if [ $? -ne 0 ]; then
		inc_failed
		lttng destroy
		return 1
	fi

	lttng destroy
	check $? "lttng destroy"
	if [ $? -ne 0 ]; then
		inc_failed
		return 1
	fi

	babeltrace ${SESSION}* > $TMPFILE
	dds=$(grep prev_comm $TMPFILE | grep dd | wc -l | cut -d' ' -f1)
	cats=$(grep prev_comm $TMPFILE | grep cat | wc -l | cut -d' ' -f1)
	echo "Found $dds dd and $cats context switches"

	if [ $dds -lt 1 ]; then
		echo "FAILED (did not trace any dd context switches)"
		inc_failed
		rc=1
		return 1
	fi
	if [ $cats -lt 1 ]; then
		echo "FAILED (did not trace any cat context switches)"
		inc_failed
		rc=1
		return 1
	fi
	echo "PASSED (simple system call tracing with babeltrace)"
	return 0
}

rc=0
test_lttng_session_create
echo " "

#
# Disabled for all kernels as this is broken for all kernels > 4.8-rc1.
# See LP#1802495
#
#test_lttng_list_kernel
#echo " "

#
# Disabled because of LP#1671063, https://bugs.lttng.org/issues/1091
#   - vmalloc failure causes the kernel syscall list to fail on
#     some architectures at the moment
#
#test_lttng_list_kernel_syscall
#echo " "

#
# Disabled for s390x, this is broken because of syscall tracing vmalloc
# issues (as above).
# Also disabled for all kernels as this is broken for all kernels > 4.8-rc1.
# See LP#1802495
#
#test_lttng_open_close
#echo " "

test_lttng_context_switch
echo " "

rm -rf $TMPFILE $SESSION

echo "Summary: $passed passed, $failed failed"

exit $rc
