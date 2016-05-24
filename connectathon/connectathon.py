import os
import shutil
import glob
import logging
import platform
from autotest.client import test, utils
from autotest.client.shared import error


class connectathon(test.test):

    """
    Connectathon test is an nfs testsuite which can run on
    both BSD and System V based systems. The tests.init file
    has to be modified based on the OS in which this test is run.

    The tar file in this dir has an init file which works for Linux
    platform.

    @see www.connectathon.org
    @author Poornima.Nayak (Poornima.Nayak@in.ibm.com)(original code)
    """
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        """
        Sets the overall failure counter for the test.
        """
        self.install_required_pkgs()
        self.nfail = 0

    def setup(self, tarball='connectathon.tar.bz2'):
        connectathon_tarball = utils.unmap_url(self.bindir, tarball,
                                               self.tmpdir)
        utils.extract_tarball_to_dir(connectathon_tarball, self.srcdir)

        os.chdir(self.srcdir)
        utils.system('patch -p1 < %s/connectathon.diff' % self.bindir)
        utils.system('make clean')
        utils.system('make')

    def run_once(self, testdir=None, args='', cthon_iterations=1):
        """
        Runs the test, with the appropriate control file.
        """
        os.chdir(self.srcdir)

        if testdir is None:
            testdir = self.tmpdir

        self.results_path = os.path.join(self.resultsdir,
                                         'raw_output_%s' % self.iteration)

        try:
            if not args:
                # run basic test
                args = "-b -t"

            self.results = utils.system_output('./runtests -N %s %s %s' % (cthon_iterations, args, testdir))
            utils.open_write_close(self.results_path, self.results)

        except error.CmdError, e:
            self.nfail += 1
            logging.error("Test failed: %s", e)

    def postprocess(self):
        """
        Raises on failure.
        """
        if self.nfail != 0:
            raise error.TestFail('Connectathon test suite failed.')
