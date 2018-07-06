import os
from autotest.client import test, utils

class qrt(test.test):
    version = 1

    def initialize(self):
        pass

    def setup(self, tarball = 'qrt.tar.bz2'):
        self.job.require_gcc()
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)

    def run_once(self, test_name):
        scripts = os.path.join(self.srcdir, 'scripts')
        os.chdir(scripts)

        if test_name == 'setup':
            return

        cmd = 'python ./%s -v' % test_name
        self.results = utils.system_output(cmd, retain_output=True)


# vi:set ts=4 sw=4 expandtab:
