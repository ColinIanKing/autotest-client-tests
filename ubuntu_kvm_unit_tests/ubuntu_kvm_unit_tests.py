import os
import sys
import platform
from autotest.client            import test, utils, os_dep
from autotest.client.shared     import error

class ubuntu_kvm_unit_tests(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential', 'qemu-kvm',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()
        self.job.require_gcc()

    def setup(self, tarball='kvm-unit-tests.tar.bz2'):
        arch = platform.processor()
        opt = []
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)
        if arch == 'ppc64le':
            opt.append('--endian={}'.format(sys.byteorder))
        utils.configure(' '.join(opt))
        utils.make()

        # patch run_tests.sh to build our tests list
        utils.system('patch -p1 < %s/runtime_show.patch' % self.bindir)
        utils.system('./run_tests.sh -v > tests.txt')

    def run_once(self, test_name, cmd=''):
        os.chdir(self.srcdir)
        if test_name == 'setup':
            return

        arch = platform.processor()
        if arch == 'ppc64le':
            # disable smt (simultaneous multithreading) on ppc for kvm
            utils.system('ppc64_cpu --smt=off')

        self.results = utils.system_output(cmd, retain_output=True, timeout=60)
        if arch == 'ppc64le':
            # turn smt back on
            utils.system('ppc64_cpu --smt=on')

# vi:set ts=4 sw=4 expandtab:

