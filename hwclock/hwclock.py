from autotest.client import test, utils
from autotest.client.shared import error
import re
import os
import logging
import platform


class hwclock(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()

    def run_once(self):
        """
        Set hwclock back to a date in 1980 and verify if the changes took
        effect in the system.
        """
        series = platform.dist()[2]
        utils.system_output('apt-get install virt-what --assume-yes', retain_output=True)
        self.virt = utils.system_output('virt-what', retain_output=True)
        #
        #  Only run if on bare metal, if what is not empty we
        #  are in some kind of VM or container
        #
        if self.virt != '':
            logging.info('Running inside ' + self.virt + ', not testing ')
        else:
            logging.info('Setting hwclock to 2/2/80 03:04:00')
            utils.system_output('/sbin/hwclock --set --date "2/2/80 03:04:00"', retain_output=True)
            date = utils.system_output('LC_ALL=C /sbin/hwclock')
            if series in ['precise', 'trusty', 'vivid', 'xenial']:
                if not re.match('Sat *Feb *2 *03:04:.. 1980', date):
                    raise error.TestFail("Failed to set hwclock back to the eighties. Output of hwclock is '%s'" % date)
            elif not re.match('1980-02-02 03:04:..*', date):
                raise error.TestFail("Failed to set hwclock back to the eighties. Output of hwclock is '%s'" % date)

    def cleanup(self):
        """
        Restore hardware clock to current system time.
        """
        if self.virt == '':
            logging.info('Restoring the hardware clock')
            utils.system('/sbin/hwclock --systohc --noadjfile --utc')
