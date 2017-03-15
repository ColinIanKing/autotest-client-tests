#
#
from autotest.client import test, utils
import platform
import os

class ubuntu_bpf(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential', 'git',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()
        self.job.require_gcc()

    def run_once(self, test_name):
        series = platform.dist()[2]
        os.chdir(self.srcdir)

        if not os.path.exists('linux'):
            cmd = 'git clone --depth=1 https://git.launchpad.net/~ubuntu-kernel/ubuntu/+source/linux/+git/%s linux' % series
            utils.system(cmd)

        cmd = '%s/ubuntu_bpf.sh %s %s' % (self.bindir, self.srcdir, self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)

        print(self.results)

# vi:set ts=4 sw=4 expandtab syntax=python:
