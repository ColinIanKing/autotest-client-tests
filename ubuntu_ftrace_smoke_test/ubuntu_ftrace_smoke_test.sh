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
#  Trival "smoke test" ftrace tests just to see
#  if basic functionality works
#
TMPFILE=/tmp/ftrace-kernel-trace-$$.tmp
TMPFILE2=/tmp/ftrace-kernel-trace2-$$.tmp

passed=0
failed=0

inc_failed()
{
	failed=$((failed + 1))
}

inc_passed()
{
	passed=$((passed + 1))
}

mount_debugfs()
{
	if [ ! -d /sys/kernel/debug ]; then
		mount -t debugfs nodev /sys/kernel/debug
		if [ $? -ne 0 ]; then
			echo "FAILED: cannot mount /sys/kernel/debug"
			exit 1
		fi
		unmount=1
	else
		unmount=0
	fi
}

umount_debugfs()
{
	if [ $unmount -eq 1 ]; then
		umount /sys/kernel/debug
	fi
}

check()
{
	if [ $1 -eq 0 ]; then
		echo "PASSED ($2)"
		inc_passed
		return 0
	fi

	echo "FAILED ($2)"
	inc_failed
	rc=1
	return 1
}

disable_tracing()
{
	echo 0 > /sys/kernel/debug/tracing/tracing_on >& /dev/null
	sleep 1
	echo "nop" > /sys/kernel/debug/tracing/current_tracer >& /dev/null
	sleep 1
}

timer_start()
{
	local pid=$$
	(sleep $1
	 echo TIMER END $(date)
	 echo "TIMEOUT"
	 echo "FAILED: aborting, timeout, took way too long to complete"
	 disable_tracing
	 exit 1
	) &
	timer_pid=$!
}

timer_stop()
{
	kill -9 $timer_pid 2> /dev/null
	wait $timer_pid 2> /dev/null
}

test_tracing_files_exist()
{
	ok=1
	files=(current_tracer available_tracers tracing_on trace \
	       trace_pipe trace_options options tracing_max_latency \
	       tracing_thresh buffer_size_kb buffer_total_size_kb \
	       free_buffer tracing_cpumask set_ftrace_filter \
	       set_ftrace_notrace set_ftrace_pid set_graph_function \
	       available_filter_functions enabled_functions \
	       function_profile_enabled max_graph_depth printk_formats \
	       saved_cmdlines snapshot stack_max_size stack_trace \
	       stack_trace_filter trace_clock trace_marker instances events)
	for f in "${files[@]}"
	do
		if [ ! -e /sys/kernel/debug/tracing/$f ]; then
			echo "FAILED /sys/kernel/debug/tracing/$f does not exist"
			inc_failed
			rc=1
			ok=0
		fi
	done

	if [ $ok -eq 1 ]; then
		echo "PASSED all expected /sys/kernel/debug/tracing files exist"
		inc_passed
	fi
}

test_available_tracers_exist()
{
	#
	# Must have the basic 3 tracers for minimal support
	#
	tracers="function_graph function nop"
	for t in $tracers
	do
		grep $t /sys/kernel/debug/tracing/available_tracers  >& /dev/null
		check $? "$t in /sys/kernel/debug/tracing/available_tracers"
	done
}

test_enable_all_tracers()
{
	disable_tracing
	for t in $(cat /sys/kernel/debug/tracing/available_tracers)
	do
		#
		# The nop tracer does nothing and turns off tracing,
		# so skip it.  Also skip wakeup* tracers as these may
		# not generate enough events on some architectures
		#
		case "$t" in
			nop|wakeup*)
				continue
				;;
			*)
				;;
		esac

		timer_start 240
		n=0
		echo $t > /sys/kernel/debug/tracing/current_tracer
		r=$?
		if [ $r -eq 0 ]; then
			echo 1 > /sys/kernel/debug/tracing/tracing_on

			touch $TMPFILE2
			#
			#  Force some activity
			#
			(dd if=/dev/zero bs=1024 count=4096 | dd of=$TMPFILE bs=1024 conv=sync) >& /dev/null &
			pid=$!
			(dd if=/sys/kernel/debug/tracing/trace bs=1024 count=64 of=$TMPFILE2 conv=sync) >& /dev/null &
			pid_trace=$!
			count=0
			while true
			do
				n=$(wc -l ${TMPFILE2} | cut -d' ' -f1)
				if [ $n -gt 0 ]; then
					echo " - tracer $t got enough data"
					break
				fi
				if [ ! -d /proc/$pid -a ! -d /proc/$pid_trace ]; then
					echo " - tracer $t data copying processes ended"
					break;
				fi
				count=$((count + 1))
				if [ $count -gt 180 ]; then
					echo " - tracer $t timed out"
					break;
				fi
				sleep 1
			done

			echo " - tracer $t completed"
			kill -9 $pid 2> /dev/null
			wait $pid 2> /dev/null

			kill -9 $pid_trace 2> /dev/null
			wait $pid_trace 2> /dev/null

			rm -f ${TMPFILE} ${TMPFILE2}
			echo " - tracer $t being turned off"
			echo 0 > /sys/kernel/debug/tracing/tracing_on
			echo " - tracer nop being set as current tracer"
			echo nop > /sys/kernel/debug/tracing/current_tracer
		fi
		disable_tracing
		check $r "tracer $t can be enabled (got $n lines of tracing output)"
		timer_stop
	done
}

test_function_graph_tracer()
{
	threshold=16
	count=0
	timer_start 240

	disable_tracing

	t="function_graph"
	echo $t > /sys/kernel/debug/tracing/current_tracer
	check $? "tracer $t can be enabled"
	echo 1 > /sys/kernel/debug/tracing/tracing_on
	dd if=/sys/kernel/debug/tracing/trace_pipe bs=1024 count=1024 conv=sync of=${TMPFILE}.log 2> /dev/null &
	pid=$!
	while true
	do
		if [ ! -d /proc/$pid ]; then
			echo " - tracer $t data copying processes ended"
			break;
		fi

		n=$(grep irq ${TMPFILE}.log | grep "()" | wc -l ${TMPFILE}.log | cut -d' ' -f1)
		if [ $n -gt $threshold ]; then
			echo " - tracer $t got enough data"
			break;
		fi

		sleep 1

		count=$((count + 1))
		if [ $count -gt 180 ]; then
			echo " - tracer $t timed out"
			break;
		fi
	done
	echo " - tracer function_graph completed"
	kill -9 $pid 2> /dev/null
	wait $pid 2> /dev/null

	echo " - tracer function_graph being turned off"
	echo 0 > /sys/kernel/debug/tracing/tracing_on
	n=$(grep irq ${TMPFILE}.log | grep "()" | wc -l ${TMPFILE}.log | cut -d' ' -f1)
	echo " - tracer got $n irq events"

	rm -f $TMPFILE ${TMPFILE}.log
	timer_stop
}

test_function_tracer()
{
	timer_start 240

	disable_tracing

	echo "function" > /sys/kernel/debug/tracing/current_tracer
	check $? "tracer function can be enabled"

	timer_stop
}

test_kernel_configs()
{
	configs="CONFIG_FUNCTION_TRACER CONFIG_FUNCTION_GRAPH_TRACER CONFIG_STACK_TRACER CONFIG_DYNAMIC_FTRACE"
	for c in $configs
	do
		grep "$c=y" /boot/config-$(uname -r) >& /dev/null
		check $? "$c=y in /boot/config-$(uname -r)"
	done
}

test_kernel_configs
mount_debugfs

#
# sys/kernel/debug/tracing should exist
#
if [ ! -d /sys/kernel/debug/tracing ]; then
	echo "FAILED: /sys/kernel/debug/tracing does not exist"
	umount_debugfs
	exit 1
fi

rc=0

disable_tracing
test_tracing_files_exist
test_available_tracers_exist
test_function_tracer
test_function_graph_tracer
test_enable_all_tracers
disable_tracing

rm -rf $TMPFILE

echo "Summary: $passed passed, $failed failed"

umount_debugfs

exit $rc
