import os
from autotest.client            import test, utils, os_dep
from autotest.client.shared     import error

class ubuntu_kvm_unit_tests(test.test):
    version = 1

    def initialize(self):
        self.job.require_gcc()

    def setup(self, tarball='kvm-unit-tests.tar.bz2'):
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)
        utils.configure() 
        utils.make()

        # patch x86/unittests.cfg
        utils.system('patch -p1 < %s/unittests.patch' % self.bindir)

    def run_once(self):
        os.chdir(self.srcdir)
        self.results = utils.system_output('./run_tests.sh', retain_output=True, timeout=240)

# vi:set ts=4 sw=4 expandtab:
