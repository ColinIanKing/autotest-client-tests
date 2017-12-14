import os
import platform
from autotest.client import test, utils

class ubuntu_ecryptfs(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'bzr', 'build-essential', 'libglib2.0-dev', 'intltool', 'keyutils', 'libkeyutils-dev', 'libpam0g-dev', 'libnss3-dev', 'libtool', 'acl', 'xfsprogs', 'btrfs-tools', 'libattr1-dev'
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()
        self.job.require_gcc()

    def setup(self):
        utils.system('bzr branch --use-existing-dir lp:ecryptfs %s' % self.srcdir)
        print(utils.system_output('bzr log %s | head' % self.srcdir, retain_output=True))

        os.chdir(self.srcdir)
        utils.system('patch -p1 < %s/run_one.patch' % self.bindir)
        utils.system('chmod +x tests/run_one.sh')
        utils.system('autoreconf -ivf')
        utils.system('intltoolize -c -f')
        utils.configure('--enable-tests --disable-pywrap')
        utils.make()

    def run_once(self, test_name, fs_type):
        os.chdir(self.srcdir)

        if test_name == 'setup':
            return

        cmd = 'tests/run_one.sh -K -t %s -b 1000000 -D /mnt/image -l /mnt/lower -u /mnt/upper -f %s' % (test_name, fs_type)
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab:
