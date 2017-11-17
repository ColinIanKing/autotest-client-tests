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
OVERLAY="250.0.0.0/8"
TMP=/tmp/fan-$$.tmp

enable_fan()
{
	fanatic enable-fan -u $UNDERLAY -o $OVERLAY > /dev/null
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAILED (fanatic enable-fan returned $ret)"
		exit 1
	fi
}

disable_fan()
{
	fanatic disable-fan -u $UNDERLAY -o $OVERLAY > /dev/null
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAILED (fanctl returned $ret)"
		exit 1
	fi
}

enable_docker()
{
	fanatic enable-docker -u $UNDERLAY -o $OVERLAY > /dev/null
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAILED (fanatic enable-docker returned $ret)"
		exit 1
	fi
}

disable_docker()
{
	fanatic disable-docker -u $UNDERLAY -o $OVERLAY > /dev/null
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAILED (fanatic enable-docker returned $ret)"
		exit 1
	fi
}

enable_disable_test()
{
	echo -n "enable disable fan test: "
	enable_fan
	disable_fan
	echo "PASSED"
}

fanctl_show_simple_test()
{
	echo -n "fanctl show test: "
	enable_fan
	fanctl show > $TMP
	ret=$?
	disable_fan
	rm -f $TMP
	if [ $ret -ne 0 ]; then
		echo "FAILED (fanctl show returned $ret)"
		exit 1
	fi
	echo "PASSED"
}

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

fanatic_enable_docker_test()
{
	echo -n "fanatic enable docker test: "
	fanatic enable-docker -o $
}

fanatic_docker_test()
{
	echo -n "fanatic docker test"
	enable_fan

	info=$(ip address | ./extract-fan-info)
	fan=$(echo $info | cut -d: -f1)
	fan_addr=$(echo $info | cut -d: -f2)
	enable_docker
	service docker restart

	# Docker needs DNS hinting if systemd-resolvd is in charge
	dns_opt=""
	dns1=$(awk '$1=="nameserver"{print $2; exit}' /etc/resolv.conf)
	if [ "$dns1" = "127.0.0.53" ]; then
		dns_opt="--dns=$(systemd-resolve --status |
			awk '/DNS Servers:/{
				sub(/.*DNS Servers: */, "")
				sub(/,.*/, "")
				print
				exit}')"
		echo -n "($dns_opt): "
	else
		echo -n ": "
	fi
	docker run $dns_opt $image sh -c "apt-get update && apt-get install iputils-ping -y && ping -c 10 $fan_addr" > $TMP
	ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAILED: (docker run returned $ret)"
		disable_docker
		disable_fan
		rm $TMP
		exit 1
	fi
	if [ $(grep "bytes from $fan_addr" $TMP | wc -l) -ne 10 ]; then
		echo "FAILED: (ping from container to $fan_addr failed)"
		disable_docker
		disable_fan
		rm $TMP
		exit 1
	fi

	disable_docker
	service docker restart
	disable_fan
	rm $TMP
	echo "PASSED"
}

UNDERLAY=$1
if [ "$UNDERLAY" = "" ]; then
	echo "FAILED (could not determine an UNDERLAY address range)"
	exit 1
fi

image="`uname -m`/ubuntu"
[ "`uname -m`" = "x86_64" ] && image="ubuntu"
echo -n "docker pull $image: "

docker pull $image > /dev/null
ret=$?
if [ $ret -ne 0 ]; then
	echo "FAILED (docker pull returned $ret)"
	exit 1
fi
echo "PASSED"

enable_disable_test
fanctl_show_simple_test
fanctl_check_bridge_test
fanatic_docker_test
