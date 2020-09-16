import os
import platform
from autotest.client import test, utils


class fs_mark(test.test):
    version = 1

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

        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    # http://developer.osdl.org/dev/doubt/fs_mark/archive/fs_mark-3.2.tgz
    def setup(self, tarball='fs_mark-3.2.tgz'):
        self.install_required_pkgs()
        self.job.require_gcc()
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)

        utils.make()

    def run_once(self, dir, args=None):
        if not args:
            # Just provide a sample run parameters
            args = '-s 10240 -n 1000'
        os.chdir(self.srcdir)
        utils.system('./fs_mark -d %s %s' % (dir, args))
