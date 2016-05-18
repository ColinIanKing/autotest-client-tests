import os
import platform
import time
from autotest.client import test, utils

class ubuntu_qrt_apparmor(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'pyflakes',
            'libcap2-bin',
            'gawk',
            'execstack',
            'exim4',
            'libcap-dev',
            'python-pexpect',
            'apparmor',
            'apparmor-utils',
            'netcat',
            'sudo',
            'libapparmor-dev',
            'attr',
            'apport',
            'libpam-apparmor',
            'libgtk2.0-dev',
            'apparmor-profiles',
            'quilt',
            'libdbus-1-dev',
            'python3',
            'python3-all-dev',
            'python-libapparmor',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64'] else 'gcc-multilib'
        pkgs.append(gcc)

        if series == 'precise':
            for p in ['ruby1.8']:
                pkgs.append(p)
        else:
            for p in ['python3-libapparmor', 'ruby', 'apparmor-easyprof']:
                pkgs.append(p)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        # Yes, the following is a horrible hack.
        #
        utils.system_output('apt-get update', retain_output=True)
        time.sleep(60)
        utils.system_output('apt-get update', retain_output=True)

        self.install_required_pkgs()
        self.job.require_gcc()

    def setup(self, tarball='ubuntu-qrt-apparmor.tar.bz2'):
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        print(utils.system_output('head %s/scripts/bzr.log' % self.srcdir, retain_output=True))

    def run_once(self, test_name):
        scripts = os.path.join(self.srcdir, 'scripts')
        os.chdir(scripts)

        if test_name == 'setup':
            return

        cmd = 'python ./%s -v' % test_name
        self.results = utils.system_output(cmd, retain_output=True)


# vi:set ts=4 sw=4 expandtab:
