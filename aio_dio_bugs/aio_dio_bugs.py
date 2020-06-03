import os
from autotest.client import test, utils
import platform


class aio_dio_bugs(test.test):
    version = 5
    preserve_srcdir = True

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        self.job.setup_dep(['libaio'])
        ldflags = '-L ' + self.autodir + '/deps/libaio/lib'
        cflags = '-I ' + self.autodir + '/deps/libaio/include'
        self.gcc_flags = ldflags + ' ' + cflags
        os.chdir(self.srcdir)
        utils.make('"CFLAGS=' + self.gcc_flags + '"')

    def run_once(self, test_name, args=''):
        os.chdir(self.tmpdir)
        libs = self.autodir + '/deps/libaio/lib/'
        ld_path = utils.prepend_path(libs,
                                     utils.environ('LD_LIBRARY_PATH'))
        var_ld_path = 'LD_LIBRARY_PATH=' + ld_path
        cmd = self.srcdir + '/' + test_name + ' ' + args
        utils.system(var_ld_path + ' ' + cmd)
