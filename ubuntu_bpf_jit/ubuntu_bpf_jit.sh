#!/bin/bash

#
# Copyright (C) 2016 Canonical
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
MODULE=test_bpf

parse_dmesg()
{
	dmesg | grep test_bpf
	#
	# Get stats, e.g.
	# [ 2936.055026] test_bpf: Summary: 305 PASSED, 0 FAILED, [0/297 JIT'ed]
	#
	passed=$(dmesg | cut -c16- | grep "test_bpf" | grep Summary | awk '{print $3}')
	failed=$(dmesg | cut -c16- | grep "test_bpf" | grep Summary | awk '{print $5}')

	echo "PASSED: $passed"
	echo "FAILED: $failed"

	if [ $failed -gt 0 ]; then
		exit 1
	fi

	exit 0
}

#
#  Trival bpf jit module test
#
n=$(find /lib/modules/$(uname -r) -name ${MODULE}.ko | wc -l)
if [ $n -eq 0 ]; then
	echo "Cannot find kernel module ${MODULE}, skipping test"
	exit 0
fi

n=$(grep ${MODULE} /proc/modules | wc -l)
if [ $n -ne 0 ]; then
	modprobe -r ${MODULE}
	if [ $? -ne 0 ]; then
		echo "Module ${MODULE} already loaded and could not be removed"
		exit 0
	fi
fi

dmesg -c > /dev/null
modprobe ${MODULE}
if [ $? -ne 0 ]; then
	echo "Module ${MODULE} load failure"
	parse_dmesg
	exit 1
fi

modprobe -r ${MODULE}
if [ $? -ne 0 ]; then
	echo "Module ${MODULE} could not be removed after test"
	exit 1
fi

parse_dmesg

