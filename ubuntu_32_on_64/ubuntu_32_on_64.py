import os, shutil
import platform
from autotest.client import test, utils


class ubuntu_32_on_64(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()
        self.job.require_gcc()

    def setup(self):
        shutil.copyfile(os.path.join(self.bindir, 'forkexec.c'),
                        os.path.join(self.srcdir, 'forkexec.c'))
        os.chdir(self.bindir)
        os.chdir(self.srcdir)
        utils.system(utils.get_cc() + ' forkexec.c -m32 -o forkexec')

    def run_once(self, test_time=10, exit_on_error=True, set_time=True):
        cmd = os.path.join(self.srcdir, 'forkexec')

        args = ' date'
        utils.system(cmd + ' ' + args)

