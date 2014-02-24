import os
from autotest.client import test, utils

class ubuntu_ecryptfs(test.test):
    version = 1

    def initialize(self):
        self.job.require_gcc()

    def setup(self, tarball = 'ubuntu_ecryptfs.tar.bz2'):
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        print(utils.system_output('head %s/bzr.log' % self.srcdir, retain_output=True))

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
