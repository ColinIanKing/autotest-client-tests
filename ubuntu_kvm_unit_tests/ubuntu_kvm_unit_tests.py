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

        # patch run_tests.sh to build our tests list
        utils.system('patch -p1 < %s/run_tests_show.patch' % self.bindir)
        utils.system('./run_tests.sh -v > tests.txt')

    def run_once(self, test_name, cmd=''):
        os.chdir(self.srcdir)
        if test_name == 'setup':
            return

        self.results = utils.system_output(cmd, retain_output=True, timeout=60)

# vi:set ts=4 sw=4 expandtab:

