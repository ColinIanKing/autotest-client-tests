# POSIX test suite wrapper class. More information about the suite can be found
# at http://posixtest.sourceforge.net/
import os
import platform
from autotest.client import test, utils


__author__ = '''mohd.omar@in.ibm.com (Mohammed Omar)'''


class posixtest(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    # http://ufpr.dl.sourceforge.net/sourceforge/posixtest/posixtestsuite-1.5.2.tar.gz
    def setup(self, tarball='posixtestsuite-1.5.2.tar.gz'):
        self.install_required_pkgs()
        self.job.require_gcc()
        self.posix_tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(self.posix_tarball, self.srcdir)
        os.chdir(self.srcdir)
        # Applying a small patch that introduces some linux specific
        # linking options
        utils.system('patch -p1 < %s/posix-linux.patch' % self.bindir)
        utils.make()

    def execute(self):
        os.chdir(self.srcdir)
        utils.system('./run_tests THR')
