import os
import platform
from autotest.client import test, utils


class scrashme(test.test):

    """
    Runs the scrashme syscalls test suite. This test mode will exercise
    kernel syscalls randomically, or in a sequential fashion.

    @note: As of the current version shipped, scrashme does support the
            following options:

    --mode must be one of random, rotate, regval, struct, or capcheck
       --mode=random : pass random values in registers to random syscalls
         -s#: use # as random seed.

       --mode=rotate : rotate value through all register combinations
         -k:  pass kernel addresses as arguments.
         -u:  pass userspace addresses as arguments.
         -x#: use value as register arguments.
         -z:  use all zeros as register parameters.
         -Sr: pass struct filled with random junk.
         -Sxx: pass struct filled with hex value xx.

       --mode=capcheck:  check syscalls that call capable() return -EPERM.

       -b#: begin at offset #.
       -c#: target syscall # only.
       -N#: do # syscalls then exit.
       -P:  poison buffers before calling syscall, and check afterwards.
       -p:  pause after syscall.

    @see: http://www.codemonkey.org.uk/projects/scrashme/
    @author: Yi Yang <yang.y.yi@gmail.com>
    """
    version = 2

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'build-essential',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self, tarball='scrashme-git-snapshot-03-18-2010.tar.bz2'):
        self.install_required_pkgs()
        self.job.require_gcc()
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)
        utils.make()

    def run_once(self, args_list=''):
        if args_list:
            args = args_list
        else:
            args = '--mode rotate'

        scrashme_path = os.path.join(self.srcdir, 'scrashme')
        utils.system("%s %s" % (scrashme_path, args))
