import os, shutil
import platform
from autotest.client import test, utils


class ubuntu_leap_seconds(test.test):
    version = 1

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

        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        shutil.copyfile(os.path.join(self.bindir, 'leap_seconds.c'),
                        os.path.join(self.srcdir, 'leap_seconds.c'))
        os.chdir(self.bindir)
        os.chdir(self.srcdir)
        utils.system(utils.get_cc() + ' leap_seconds.c -D_BSD_SOURCE -D_POSIX_C_SOURCE=200112 -o leap_seconds -lrt')

    def run_once(self, test_time=10, exit_on_error=True, set_time=True):
        cmd = os.path.join(self.srcdir, 'leap_seconds')

        args = ''
        if set_time:
            args += ' -s'

        if exit_on_error:
            args += ' -x'

        args += ' -t %d' % test_time
        utils.system(cmd + ' ' + args)

