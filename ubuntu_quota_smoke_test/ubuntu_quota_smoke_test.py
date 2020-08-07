#
#
import os
import platform
import re
from autotest.client                        import test, utils

class ubuntu_quota_smoke_test(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'quota',
        ]

        flavour = re.split('-\d*-', platform.uname()[2])[-1]
        if flavour in ['aws', 'azure', 'azure-fips', 'gcp', 'gke']:
             pkgs.append('linux-modules-extra-' + flavour + '*')

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()

    def run_once(self, test_name):
        cmd = '%s/ubuntu_quota_smoke_test.sh' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)
        print(self.results)

# vi:set ts=4 sw=4 expandtab syntax=python:
