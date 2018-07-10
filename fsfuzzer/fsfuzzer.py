import os
from autotest.client import test, utils


class fsfuzzer(test.test):
    version = 1

    def initialize(self):
        pass

    # http://people.redhat.com/sgrubb/files/fsfuzzer-0.6.tar.gz
    def setup(self, tarball='fsfuzzer-0.6.tar.gz'):
        self.job.require_gcc()
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)
        utils.system('patch -p1 < %s/makefile.patch' % self.bindir)
        utils.make()

    def run_once(self, fstype='iso9660'):
        args = fstype + ' 1'
        utils.system(self.srcdir + '/run_test ' + args)
