import os
import platform
import shutil
import time
from autotest.client import test, utils

class ubuntu_qrt_apparmor(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()

        pkgs = [
            'apparmor',
            'apparmor-profiles',
            'apparmor-utils',
            'apport',
            'attr',
            'devscripts',
            'execstack',
            'exim4',
            'gawk',
            'git',
            'libapparmor-dev',
            'libapparmor-perl',
            'libcap2-bin',
            'libcap-dev',
            'libdbus-1-dev',
            'libgtk2.0-dev',
            'libpam-apparmor',
            'netcat',
            'python3',
            'python3-all-dev',
            'quilt',
            'sudo',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        if self.series == 'precise':
            for p in ['python-libapparmor', 'ruby1.8']:
                pkgs.append(p)
        elif self.series in ['trusty', 'xenial', 'bionic', 'cosmic']:
            for p in ['python-libapparmor', 'python3-libapparmor', 'ruby', 'apparmor-easyprof']:
                pkgs.append(p)
        else:
            for p in ['python3-libapparmor', 'ruby', 'apparmor-easyprof']:
                pkgs.append(p)

        if self.series in ['precise', 'trusty', 'xenial', 'bionic', 'focal']:
            pkgs.append('pyflakes')
            pkgs.append('python-pexpect')
        else:
            pkgs.append('pyflakes3')
            pkgs.append('python3-pexpect')
            pkgs.append('python3-notify2')
            pkgs.append('python3-psutil')

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        try:
            self.series = platform.dist()[2]
        except AttributeError:
            import distro
            self.series = distro.codename()
        pass

    def setup(self):
        # Yes, the following is a horrible hack.
        #
        utils.system_output('apt-get update', retain_output=True)
        time.sleep(60)
        utils.system_output('apt-get update', retain_output=True)
        self.install_required_pkgs()

        os.chdir(self.srcdir)
        shutil.rmtree('qa-regression-testing', ignore_errors=True)
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

        inter = 'python3'
        if self.series in ['precise', 'trusty', 'xenial', 'bionic', 'focal']:
            inter = 'python2'

        cmd = '%s ./%s -v' % (inter, test_name)
        self.results = utils.system_output(cmd, retain_output=True)


# vi:set ts=4 sw=4 expandtab:
