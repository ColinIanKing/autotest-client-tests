# Copyright (c) 2009 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging, os, re, string
import platform

from autotest.client import test, utils
from autotest.client.shared import error
from autotest.client.ubuntu.wifi import WiFi

class network_WiFiCaps(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'iw', 'pkg-config', 'libnl-dev',
        ]

        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()

        self.job.setup_dep(['iwcap'])
        # create a empty srcdir to prevent the error that checks .version
        if not os.path.exists(self.srcdir):
            os.mkdir(self.srcdir)

    def __parse_iwcap(self, lines):
        """Parse the iwcap output"""

        results = {}
        parse_re = re.compile(r'([a-z0-9]*):[ ]*(.*)')
        for line in lines.split('\n'):
            line = line.rstrip()
            logging.info('==> %s' %line)
            match = parse_re.search(line)
            if match:
                results[match.group(1)] = match.group(2)
                continue
        return results


    def __run_iwcap(self, phy, caps):
        dir = os.path.join(self.autodir, 'deps', 'iwcap', 'iwcap')
        print(dir + ' ' + phy + ' ' + string.join(caps))
        iwcap = utils.run(dir + ' ' + phy + ' ' + string.join(caps))
        return self.__parse_iwcap(iwcap.stdout)

    def run_once(self):
        wifi = WiFi()
        if not wifi.exists():
            raise error.TestError('No WiFi pci device was found')

        phy = utils.system_output("iw list | awk '/^Wiphy/ {print $2}'")
        if not phy or 'phy' not in phy:
            raise error.TestError('WiFi Physical interface not found')

        requiredCaps = wifi.caps

        dep = 'iwcap'
        dep_dir = os.path.join(self.autodir, 'deps', dep)
        self.job.install_pkg(dep, 'dep', dep_dir)

        results = self.__run_iwcap(phy, requiredCaps.keys())
        for cap in requiredCaps:
            if not cap in results:
                raise error.TestError('Internal error, ' +
                    'capability "%s" not handled' % cap)
            if results[cap] != requiredCaps[cap]:
                raise error.TestError('Requirement not met: ' +
                    'cap "%s" is "%s" but expected "%s"'
                    % (cap, results[cap], requiredCaps[cap]))
