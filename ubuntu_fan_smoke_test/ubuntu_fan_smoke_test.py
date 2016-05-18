#
#
import platform
from autotest.client                        import test, utils

class ubuntu_fan_smoke_test(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential', 'gdb', 'git', 'docker.io', 'ubuntu-fan',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()

    def setup(self):
        pass

    def run_once(self, test_name):
        cmd = '%s/ubuntu_fan_smoke_test.sh' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)

        print(self.results)

# vi:set ts=4 sw=4 expandtab syntax=python:
