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
import platform
from autotest.client                        import test, utils

class ubuntu_nbd_smoke_test(test.test):
    version = 0

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'nbd-server',
            'nbd-client',
            'net-tools',
            'gdb',
        ]
        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()
        utils.system_output('rm -f /etc/*/S99autotest || true', retain_output=True)
        os.chdir(self.srcdir)

    def run_once(self, test_name):
        #
        #  stress-ng "quick fire" short life tests
        #
        cmd = self.bindir + '/ubuntu_nbd_smoke_test.sh'
        self.results = utils.system_output(cmd, retain_output=True)
        #
        # FIXME: comment this out on production
        #
        #print self.results

# vi:set ts=4 sw=4 expandtab syntax=python:
