#!/bin/sh

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

#
#  Trival "smoke test" fan tests just to see
#  if basic functionality works
#

UNDERLAY="$1"
OVERLAY="250.0.0.0/8"
TMP=/tmp/fan-$$.tmp
FAILURES=0

#export http_proxy=""
#if echo "" | nc -w 2 squid.internal 3128 >/dev/null 2>&1; then
#    echo "Running in the Canonical CI environment"
#    export http_proxy="http://squid.internal:3128"
#elif echo "" | nc -w 2 10.245.64.1 3128 >/dev/null 2>&1; then
#    echo "Running in the Canonical enablement environment"
#    export http_proxy="http://10.245.64.1:3128"
#elif echo "" | nc -w 2 91.189.89.216 3128 >/dev/null 2>&1; then
#    echo "Running in the Canonical enablement environment"
#    export http_proxy="http://91.189.89.216:3128"
#fi

#if [ -n "$http_proxy" ]; then
#    export https_proxy="$http_proxy"
#    [ ! -d /etc/systemd/system/docker.service.d ] && mkdir /etc/systemd/system/docker.service.d
#    echo -n "[Service]\nEnvironment=HTTP_PROXY=$http_proxy\n" > /etc/systemd/system/docker.service.d/http-proxy.conf
#    systemctl daemon-reload
#    systemctl restart docker
#fi

do_fanatic()
{
	local ret

	echo "- fanatic $@"
	fanatic $@ >/dev/null
	ret=$?

	if [ $ret -ne 0 ]; then
		echo "FAIL: RC=$ret)"
		FAILURES=$(($FAILURES + 1))
	fi
	return $ret
}

_assert_fanatic()
{
	local A_UNDERLAY="$1"
	local A_OVERLAY="$2"
	local A_NETSTAT="$3"
	local A_DOCSTAT="$4"
	local A_LXDSTAT="$5"
	local RC=1

	fanatic show | awk '
		BEGIN{
			RC = 1
		}
		FNR>1{
			print "  " $0
			if ( $1 != "'$A_UNDERLAY'" )
				next
			if ( $2 != "'$A_OVERLAY'" )
				next
			if ( "'$A_NETSTAT'" != "#" && $3 != "'$A_NETSTAT'" )
				next
			if ( "'$A_DOCSTAT'" != "#" && $4 != "'$A_DOCSTAT'" )
				next
			if ( "'$A_LXDSTAT'" != "#" && $5 != "'$A_LXDSTAT'" )
				next
			RC = 0
		}
		END{
			exit RC
		}'
	return $?
}

assert_fanatic()
{
	local RC

	echo "  Underlay             Overlay              Fan  Docker  LXD"
	_assert_fanatic $@
	RC=$?

	if [ $RC -ne 0 ]; then
		echo "Assertion failed! status unexpected" >&2
		echo "Expected: $@" >&2
		FAILURES=$(($FAILURES + 1))
	fi
	return $RC
}

#
# enable fan (over- and underlay specified)
#
echo
echo "enabling fan with specific over- and underlay"
if do_fanatic enable-fan -u $UNDERLAY -o $OVERLAY; then
	assert_fanatic $UNDERLAY $OVERLAY up - -
	fanctl show
	do_fanatic disable-fan -u $UNDERLAY -o $OVERLAY
	if _assert_fanatic $UNDERLAY $OVERLAY "#" "#" "#"; then
		echo "Assertion failed! Fan Network not deconfigured!" >&2
		FAILURES=$(($FAILURES + 1))
	fi
fi

echo
echo "running local docker test"
if do_fanatic enable-fan -u $UNDERLAY -o $OVERLAY; then
	if do_fanatic enable-docker -u $UNDERLAY -o $OVERLAY; then
		assert_fanatic $UNDERLAY $OVERLAY up enabled -
		#do_fanatic test local-docker -u $UNDERLAY -o $OVERLAY
		do_fanatic disable-docker -u $UNDERLAY -o $OVERLAY
		assert_fanatic $UNDERLAY $OVERLAY up - -
	fi
	do_fanatic disable-fan -u $UNDERLAY -o $OVERLAY
	if _assert_fanatic $UNDERLAY $OVERLAY "#" "#" "#"; then
		echo "Assertion failed! Fan Network not deconfigured!" >&2
		FAILURES=$(($FAILURES + 1))
	fi
fi

echo
echo "running local LXD test"
if do_fanatic enable-fan -u $UNDERLAY -o $OVERLAY; then
	if do_fanatic enable-lxd -u $UNDERLAY -o $OVERLAY; then
		assert_fanatic $UNDERLAY $OVERLAY up - enabled
		do_fanatic test local-lxd -u $UNDERLAY -o $OVERLAY
		do_fanatic disable-lxd -u $UNDERLAY -o $OVERLAY
		assert_fanatic $UNDERLAY $OVERLAY up - -
	fi
	do_fanatic disable-fan -u $UNDERLAY -o $OVERLAY
	if _assert_fanatic $UNDERLAY $OVERLAY "#" "#" "#"; then
		echo "Assertion failed! Fan Network not deconfigured!" >&2
		FAILURES=$(($FAILURES + 1))
	fi
fi

if [ $FAILURES -eq 0 ]; then
	echo "PASSED"
else
	echo "FAILED ($FAILURES failures)"
fi

exit $FAILURES

fanctl_check_bridge_test()
{
	failed=""
	echo -n "fanctl check bridge config test: "
	enable_fan
	fanctl show > $TMP
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAILED (fanctl show returned $ret)"
		exit 1
	fi

	while read bridge underlay overlay flags
	do
		if [ x$bridge != xBridge ]; then
			ifconfig $bridge > /dev/null
			if [ $? -ne 0 ]; then
				failed="$failed $bridge"
			fi
		fi
	done < $TMP

	disable_fan

	if [ ! -z $failed ]; then
		echo "FAILED (bridge:$failed)"
		exit 1
	fi

	echo "PASSED"
}

export http_proxy=""
if echo "" | nc -w 2 squid.internal 3128 >/dev/null 2>&1; then
    echo "Running in the Canonical CI environment"
    export http_proxy="http://squid.internal:3128"
elif echo "" | nc -w 2 10.245.64.1 3128 >/dev/null 2>&1; then
    echo "Running in the Canonical enablement environment"
    export http_proxy="http://10.245.64.1:3128"
elif echo "" | nc -w 2 91.189.89.216 3128 >/dev/null 2>&1; then
    echo "Running in the Canonical enablement environment"
    export http_proxy="http://91.189.89.216:3128"
fi

if [ -n "$http_proxy" ]; then
    export https_proxy="$http_proxy"
    [ ! -d /etc/systemd/system/docker.service.d ] && mkdir /etc/systemd/system/docker.service.d
    echo -n "[Service]\nEnvironment=HTTP_PROXY=$http_proxy\n" > /etc/systemd/system/docker.service.d/http-proxy.conf
    systemctl daemon-reload
    systemctl restart docker
fi
