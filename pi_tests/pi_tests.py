import os
from autotest.client import test, utils


class pi_tests(test.test):
    version = 1

    def initialize(self):
        pass

    # http://www.stardust.webpages.pl/files/patches/autotest/pi_tests.tar.bz2
    def setup(self, tarball='pi_tests.tar.bz2'):
        self.job.require_gcc()
        utils.check_glibc_ver('2.5')
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)
        utils.make()

    def execute(self, args='1 300'):
        os.chdir(self.srcdir)
        utils.system('./start.sh ' + args)
