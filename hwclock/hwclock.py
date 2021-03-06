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

        pkgs = [
            'virt-what',
        ]

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()

    def run_once(self):
        """
        Set hwclock back to a date in 2004 and verify if the changes took
        effect in the system.
        """
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()
        self.virt = utils.system_output('virt-what', retain_output=True)
        #
        #  Only run if on bare metal, if what is not empty we
        #  are in some kind of VM or container
        #
        if self.virt != '':
            logging.info('Running inside ' + self.virt + ', not testing ')
        else:
            logging.info('Setting hwclock to 2004 Oct. 20 04:10:00')
            utils.system_output('/sbin/hwclock --set --date "2004/10/20 04:10:00"', retain_output=True)
            date = utils.system_output('LC_ALL=C /sbin/hwclock')
            if series in ['precise', 'trusty', 'vivid', 'xenial']:
                if not re.match('Wed *Oct *20 *04:10:.. 2004', date):
                    raise error.TestFail("Failed to set hwclock back to Warthog's birthday. Output of hwclock is '%s'" % date)
            elif not re.match('2004-10-20 04:10:..*', date):
                raise error.TestFail("Failed to set hwclock back to Warthog's birthday. Output of hwclock is '%s'" % date)

    def cleanup(self):
        """
        Restore hardware clock to current system time.
        """
        if self.virt == '':
            logging.info('Restoring the hardware clock')
            utils.system('/sbin/hwclock --systohc --noadjfile --utc')
