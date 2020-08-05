import os
import re
import logging
import platform
from autotest.client import test, utils
from autotest.client.shared import error


class monotonic_time(test.test):
    version = 1

    preserve_srcdir = True

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        os.chdir(self.srcdir)
        utils.make()

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'build-essential',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def run_once(self, test_type=None, duration=300, threshold=None):
        if not test_type:
            raise error.TestError('missing test type')

        cmd = self.srcdir + '/time_test'
        cmd += ' --duration ' + str(duration)
        if threshold:
            cmd += ' --threshold ' + str(threshold)
        cmd += ' ' + test_type

        self.results = utils.run(cmd, ignore_status=True)
        logging.info('Time test command exit status: %s',
                     self.results.exit_status)
        if self.results.exit_status != 0:
            for line in self.results.stdout.splitlines():
                if line.startswith('ERROR:'):
                    raise error.TestError(line)
                if line.startswith('FAIL:'):
                    raise error.TestFail(line)
            raise error.TestError('unknown test failure')
