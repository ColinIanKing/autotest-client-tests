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

set -e
rc=0
BINDIR=$1
SRCDIR=$2

# FIXME: This should be done in default adt environment
# Detect the ubuntu-ci setup
if echo "" | nc -w 2 squid.internal 3128 >/dev/null 2>&1; then
    echo "Running in the Canonical CI environment"
    export http_proxy="http://squid.internal:3128"
    export https_proxy="http://squid.internal:3128"
elif echo "" | nc -w 2 10.245.64.1 3128 >/dev/null 2>&1; then
    echo "Running in the Canonical enablement environment"
    export http_proxy="http://10.245.64.1:3128"
    export https_proxy="http://10.245.64.1:3128"
elif echo "" | nc -w 2 91.189.89.216 3128 >/dev/null 2>&1; then
    echo "Running in the Canonical enablement environment"
    export http_proxy="http://91.189.89.216:3128"
    export https_proxy="http://91.189.89.216:3128"
fi

#
#  Currently bpf tests are in linux-next, these probably won't land
#  until Linux 4.10
#
git clone https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git
cd linux-next
git reset --hard 02eb3c71e393a088746de13f67be69f3555b73a2
git am ${SRCDIR}/0001-selftests-just-build-bpf.patch
git am ${SRCDIR}/0002-Fix-incomplete-type-build-error-on-struct-rlimit-by-.patch
git am ${SRCDIR}/0003-bpf-selftests-remove-test_lru_map-from-build.patch

cd tools/testing/selftests
make clean
make

#
#  Run test_verifier bpf tests
#
PID=$$
TMP=/tmp/test_verifier_${PID}.log
echo "Running test_verifier bpf test.."
if [ $EUID -eq 0 ]; then
	#
	# Drop priviledges
	#
	capsh --user=nobody -- -c bpf/test_verifier > ${TMP}
else
	#
	# We're OK as joe user
	#
	bpf/test_verifier > ${TMP}
fi
failed=$(grep FAILED ${TMP} | awk '{print $4}')

cat ${TMP}
rm -f ${TMP}

echo -n "test_verifier: "
if [ $failed -gt 0 ]; then
	echo "FAILED"
	rc=1
else
	echo "PASSED"
fi

#
#  Run test_maps bpf tests
#
if [ $EUID -ne 0 ]; then
	echo "Need to run test_maps as root, aborted"
else
	TMP=/tmp/test_maps_${PID}.log
	echo ""
	echo "Running test_maps bpf test.."
	bpf/test_maps > ${TMP}
	ok=$(grep OK ${TMP} | wc -l)
	echo -n "test_maps: "
	if [ $ok -ne 0 ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi
fi

echo " "

#
# Summary:
#
echo -n "bpf tests "
if [ $rc -eq 0 ]; then
	echo "PASSED"
else
	echo "FAILED"
fi
exit $rc

