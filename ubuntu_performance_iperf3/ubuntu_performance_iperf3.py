#
# Copyright (C) 2018 Canonical
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
import os
import shutil
from autotest.client import test, utils


class ubuntu_performance_iperf3(test.test):
    version = 0

    def install_required_pkgs(self):
        pkgs = ['dmidecode']
        cmd = 'DEBIAN_FRONTEND=noninteractive apt install -y ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        os.chdir(self.srcdir)

    def run_once(self, test_name):
        bpn = utils.system_output(
            'dmidecode -s baseboard-product-name',
            retain_output=True,
        )
        if bpn == 'NVIDIA DGX-2':
            config = 'dgx2.yaml'
        elif bpn == 'DGXA100':
            config = 'a100.yaml'
        else:
            raise KeyError("No iperf3 config file for server {}".format(bpn))

        #
        #  iperf3 performance tests on DGX2 Mellanox NIC.
        #
        shutil.copy(
            os.path.join(self.bindir, config),
            os.path.join(os.path.sep, 'tmp', config)
        )
        cmd = self.bindir + \
            '/ubuntu_iperf3_test.sh -c /tmp/{}'.format(config)
        self.results = utils.system_output(cmd, retain_output=True)
# vi:set ts=4 sw=4 expandtab syntax=python:
