# This requires aio headers to build.
# Should work automagically out of deps now.

# NOTE - this should also have the ability to mount a filesystem,
# run the tests, unmount it, then fsck the filesystem
import os
import platform
from autotest.client import test, utils


class fsx(test.test):
    version = 3

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

    # http://www.zip.com.au/~akpm/linux/patches/stuff/ext3-tools.tar.gz
    def setup(self, tarball='ext3-tools.tar.gz'):
        self.tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(self.tarball, self.srcdir)

        self.job.setup_dep(['libaio'])
        ldflags = '-L' + self.autodir + '/deps/libaio/lib'
        cflags = '-I' + self.autodir + '/deps/libaio/include'
        var_ldflags = 'LDFLAGS="' + ldflags + '"'
        var_cflags = 'CFLAGS="' + cflags + '"'
        self.make_flags = var_ldflags + ' ' + var_cflags

        os.chdir(self.srcdir)
        p1 = '0001-Minor-fixes-to-PAGE_SIZE-handling.patch'
        p2 = '0002-Enable-cross-compiling-for-fsx.patch'
        p3 = '0003-ext3-tools.patch'
        utils.system('patch -p1 < %s/%s' % (self.bindir, p1))
        utils.system('patch -p1 < %s/%s' % (self.bindir, p2))
        utils.system('patch -p1 < %s/%s' % (self.bindir, p3))
        utils.system(self.make_flags + ' make fsx-linux')

    def run_once(self, dir=None, repeat=100000):
        args = '-N %s' % repeat
        if not dir:
            dir = self.tmpdir
        os.chdir(dir)
        libs = self.autodir + '/deps/libaio/lib/'
        ld_path = utils.prepend_path(libs,
                                     utils.environ('LD_LIBRARY_PATH'))
        var_ld_path = 'LD_LIBRARY_PATH=' + ld_path
        cmd = self.srcdir + '/fsx-linux ' + args + ' poo'
        utils.system(var_ld_path + ' ' + cmd)
