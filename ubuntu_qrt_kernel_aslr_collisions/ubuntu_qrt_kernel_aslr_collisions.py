import os
import platform
from autotest.client import test, utils
from autotest.client.shared import software_manager
import platform

class ubuntu_qrt_kernel_aslr_collisions(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'git', 'build-essential', 'libcap2-bin', 'gawk', 'execstack', 'exim4', 'libcap-dev',
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
        os.chdir(self.srcdir)
        cmd = 'git clone --depth 1 https://git.launchpad.net/qa-regression-testing'
        self.results = utils.system_output(cmd, retain_output=True)
        # Print test suite HEAD SHA1 commit id for future reference
        os.chdir(os.path.join(self.srcdir, 'qa-regression-testing'))
        sha1 = utils.system_output('git rev-parse --short HEAD', retain_output=False, verbose=False)
        print("Test suite HEAD SHA1: {}".format(sha1))

    def run_once(self, test_name):
        scripts = os.path.join(self.srcdir, 'qa-regression-testing', 'scripts')
        os.chdir(scripts)

        if test_name == 'setup':
            return

        cmd = 'python2 ./%s -v' % test_name
        self.results = utils.system_output(cmd, retain_output=True)


# vi:set ts=4 sw=4 expandtab:
