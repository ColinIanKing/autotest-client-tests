import os
import platform
from autotest.client import test, utils


class flail(test.test):

    """
    This autotest module runs the flail system call fuzzer.

    Fuzzing is slang for fault injection . It runs all system calls for that
    kernel version with random args. The goal is to find bugs in software
    without reading code or designing detailed test cases.

    @author: Pradeep K Surisetty (psuriset@linux.vnet.ibm.com)
    @see: http://www.risesecurity.org/ (Website of Ramon Valle, flail's creator)
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
        self.install_required_pkgs()
        self.job.require_gcc()

    def setup(self, tarball='flail-0.2.0.tar.gz'):
        """
        Compiles flail with the appropriate parameters.

        :param tarball: Path or URL for the flail tarball.
        """
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)
        utils.system('patch -p1 < %s/makefile.patch' % self.bindir)
        utils.make()

    def run_once(self, fstype='iso9660'):
        """
        Runs flail with the appropriate parameters.

        :param fstype: Filesystem type you wish to run flail on.
        """
        args = fstype + ' 1'
        flail_cmd = os.path.join(self.srcdir, 'flail %s' % args)
        utils.system(flail_cmd)
