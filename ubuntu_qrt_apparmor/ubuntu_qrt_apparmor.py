import os
import platform
import time
from autotest.client import test, utils

class ubuntu_qrt_apparmor(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

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

        if series == 'precise':
            for p in ['python-libapparmor', 'ruby1.8']:
                pkgs.append(p)
        elif series in ['trusty', 'xenial', 'bionic', 'cosmic']:
            for p in ['python-libapparmor', 'python3-libapparmor', 'ruby', 'apparmor-easyprof']:
                pkgs.append(p)
        else:
            for p in ['python3-libapparmor', 'ruby', 'apparmor-easyprof']:
                pkgs.append(p)

        if series in ['precise', 'trusty', 'xenial', 'bionic', 'focal']:
            pkgs.append('pyflakes')
            pkgs.append('python-pexpect')
        else:
            pkgs.append('pyflakes3')
            pkgs.append('python3-pexpect')

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        # Yes, the following is a horrible hack.
        #
        utils.system_output('apt-get update', retain_output=True)
        time.sleep(60)
        utils.system_output('apt-get update', retain_output=True)
        self.install_required_pkgs()

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
