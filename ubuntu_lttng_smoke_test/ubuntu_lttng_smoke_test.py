#
#
import platform
from autotest.client                        import test, utils
from autotest.client.shared                 import error

class ubuntu_lttng_smoke_test(test.test):
    version = 99

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential',
            'babeltrace',
            'lttng-tools',
            'lttng-modules-dkms',
            'liblttng-ust-dev',
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
        cmd = 'dkms status -m lttng-modules | grep installed'
        try:
            utils.system(cmd)
        except error.CmdError:
            cmd = 'cat /var/lib/dkms/lttng-modules/*/build/make.log'
            utils.system(cmd)
            raise error.TestError('DKMS failed to install')

    def run_once(self, test_name):
        cmd = '%s/ubuntu_lttng_smoke_test.sh' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)
        print self.results

    def cleanup(self):
        cmd = 'apt-get remove --yes lttng-modules-dkms'
        self.results = utils.system_output(cmd, retain_output=False)

# vi:set ts=4 sw=4 expandtab syntax=python:
