import os
import platform
from autotest.client import test, utils

class ubuntu_qrt_kernel_security(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'git', 'build-essential', 'libcap2-bin', 'gawk', 'execstack', 'exim4', 'libcap-dev', 'libkeyutils-dev',
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
        os.chdir(self.srcdir)
        cmd = 'git clone --depth 1 https://git.launchpad.net/qa-regression-testing'
        self.results = utils.system_output(cmd, retain_output=True)

    def run_once(self, test_name):
        scripts = os.path.join(self.srcdir, 'qa-regression-testing', 'scripts')
        os.chdir(scripts)

        if test_name == 'setup':
            return

        cmd = 'python ./%s -v' % test_name
        self.results = utils.system_output(cmd, retain_output=True)


# vi:set ts=4 sw=4 expandtab:
