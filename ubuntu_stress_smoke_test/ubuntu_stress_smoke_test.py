#
#
import os
from autotest.client                        import test, utils
import platform

class ubuntu_stress_smoke_test(test.test):
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
        pass

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        cmd = 'apt-get install zlib1g-dev libbsd-dev libattr1-dev libkeyutils-dev libapparmor-dev apparmor libaio-dev --assume-yes --allow-downgrades --allow-change-held-packages'
        utils.system_output(cmd, retain_output=True)
        os.chdir(self.srcdir)
        cmd = 'git clone git://kernel.ubuntu.com/cking/stress-ng'
        self.results = utils.system_output(cmd, retain_output=True)
        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        self.results = utils.system_output('make', retain_output=True)

    def run_once(self, test_name):
        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        cmd = '%s/ubuntu_stress_smoke_test.sh' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)

        print(self.results)

# vi:set ts=4 sw=4 expandtab syntax=python:
