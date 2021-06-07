import multiprocessing
import os
import sys
import re
import platform
import shutil
from autotest.client            import test, utils, os_dep
from autotest.client.shared     import error
from autotest.client            import canonical

class ubuntu_kvm_unit_tests(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'build-essential', 'cpu-checker', 'qemu-kvm', 'git',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        canonical.setup_proxy()
        self.install_required_pkgs()
        self.job.require_gcc()

        arch = platform.processor()
        opt = []
        os.chdir(self.srcdir)
        shutil.rmtree('kvm-unit-tests', ignore_errors=True)
        cmd = 'git clone --depth=1 git://kernel.ubuntu.com/ubuntu/kvm-unit-tests/ -b disco'
        self.results = utils.system_output(cmd, retain_output=True)
        # Print test suite HEAD SHA1 commit id for future reference
        os.chdir(os.path.join(self.srcdir, 'kvm-unit-tests'))
        sha1 = utils.system_output('git rev-parse --short HEAD', retain_output=False, verbose=False)
        print("Test suite HEAD SHA1: {}".format(sha1))

        # patch run_tests.sh to get rid of the color output
        utils.system('patch -p1 < %s/runtime_show.patch' % self.bindir)

        if arch == 'ppc64le':
            opt.append('--endian={}'.format(sys.byteorder))
        utils.configure(' '.join(opt))
        try:
            nprocs = '-j' + str(multiprocessing.cpu_count())
        except:
            nprocs = ''
        utils.make(nprocs + ' standalone')

    def run_once(self, test_name):
        if test_name == 'setup':
            return

        try:
            utils.system('kvm-ok')
            arch = platform.processor()
            if arch == 'ppc64le':
                # disable smt (simultaneous multithreading) on ppc for kvm
                utils.system('ppc64_cpu --smt=off')

            cmd = os.path.join(self.srcdir, 'kvm-unit-tests/tests', test_name)
            output = utils.system_output(cmd, ignore_status=True, retain_output=True)

            if arch == 'ppc64le':
                # turn smt back on
                utils.system('ppc64_cpu --smt=on')

            # The SKIP status will be treated as PASS as well.
            if output.split('\n')[-1].startswith('FAIL'):
                raise error.TestError("Test failed for {}".format(test_name))

        except error.CmdError:
            print('Test skipped, this systems does not have KVM extension support')


# vi:set ts=4 sw=4 expandtab:
