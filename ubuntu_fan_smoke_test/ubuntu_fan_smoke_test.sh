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

FAN_VERSION="$(apt-cache policy ubuntu-fan|awk '/Installed:/{print $2}')"
RUN_DIR="$(dirname $0)"

http_proxy=""
https_proxy=""
if echo "" | nc -w 2 squid.internal 3128 >/dev/null 2>&1; then
    INFO="Running in the Canonical CI environment"
    http_proxy="http://squid.internal:3128"
    https_proxy="http://squid.internal:3128"
elif echo "" | nc -w 2 91.189.89.216 3128 >/dev/null 2>&1; then
    INFO="Running in the Canonical enablement environment (proxy1)"
    http_proxy="http://91.189.89.216:3128"
    https_proxy="http://91.189.89.216:3128"
elif echo "" | nc -w 2 10.245.64.1 3128 >/dev/null 2>&1; then
    INFO="Running in the Canonical enablement environment (proxy2"
    http_proxy="http://10.245.64.1:3128"
    https_proxy="http://10.245.64.1:3128"
fi
export http_proxy
export https_proxy

URI="http://index.docker.io/v1/repositories/library/ubuntu/images"
if wget -q -O/dev/null $URI; then
    echo $INFO
else
    unset http_proxy
    unset https_proxy
fi

if [ -n "$http_proxy" ]; then
    if [ ! -d /etc/systemd/system/docker.service.d ]; then
        mkdir /etc/systemd/system/docker.service.d
    fi
    case $(readlink /bin/sh) in
        dash)
            EOPTS="-n"
            ;;
        *)
            EOPTS="-ne"
            ;;
    esac

    mkdir -p /etc/systemd/system/containerd.service.d
    touch /etc/systemd/system/containerd.service.d/override.conf
    echo -e "[Service]\nExecStartPre=" >> /etc/systemd/system/containerd.service.d/override.conf
    systemctl daemon-reload
    systemctl restart docker.service

    echo $EOPTS "[Service]\nEnvironment=\"HTTP_PROXY=$http_proxy\"\n" \
         > /etc/systemd/system/docker.service.d/http-proxy.conf
    systemctl daemon-reload
    systemctl restart docker.service
fi

if dpkg --compare-versions $FAN_VERSION lt 0.13; then
	echo "Testing Fan Networking (pre-0.13.0 API)"
	$RUN_DIR/smoke_test_old.sh "$@"
	RC=$?
else
	echo "Testing Fan Networking (0.13.0+ API)"
	$RUN_DIR/smoke_test-0.13.0.sh "$@"
	RC=$?
fi

exit $RC

