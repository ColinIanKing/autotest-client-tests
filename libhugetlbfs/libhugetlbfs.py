import re
import os
import platform
import shutil
from autotest.client import utils, test, os_dep
from autotest.client.shared import error


class libhugetlbfs(test.test):
    version = 7

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'build-essential',
            'git',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self, hugetlbfs_dir=None, pages_requested=20):
        self.hugetlbfs_dir = None

        # check if basic utilities are present
        utils.check_kernel_ver("2.6.16")

        # Check huge page number
        pages_available = 0
        if os.path.exists('/proc/sys/vm/nr_hugepages'):
            utils.write_one_line('/proc/sys/vm/nr_hugepages',
                                 str(pages_requested))
            nr_hugepages = utils.read_one_line('/proc/sys/vm/nr_hugepages')
            pages_available = int(nr_hugepages)
        else:
            raise error.TestNAError('Kernel does not support hugepages')

        if pages_available < pages_requested:
            raise error.TestError('%d pages available, < %d pages requested'
                                  % (pages_available, pages_requested))

        # Check if hugetlbfs has been mounted
        if not utils.file_contains_pattern('/proc/mounts', 'hugetlbfs'):
            if not hugetlbfs_dir:
                hugetlbfs_dir = os.path.join(self.tmpdir, 'hugetlbfs')
                os.makedirs(hugetlbfs_dir)
            utils.system('mount -t hugetlbfs none %s' % hugetlbfs_dir)
            self.hugetlbfs_dir = hugetlbfs_dir

    def setup(self):
        self.install_required_pkgs()
        os_dep.library('libpthread.a')
        self.job.require_gcc()
        # get the sources
        os.chdir(self.srcdir)
        shutil.rmtree('libhugetlbfs', ignore_errors=True)
        cmd = 'git clone --depth=1 -b next https://github.com/libhugetlbfs/libhugetlbfs.git'
        self.results = utils.system_output(cmd, retain_output=True)

        # Print test suite HEAD SHA1 commit id for future reference
        os.chdir(os.path.join(self.srcdir, 'libhugetlbfs'))
        sha1 = utils.system_output('git rev-parse --short HEAD', retain_output=False, verbose=False)
        print("Test suite HEAD SHA1: {}".format(sha1))
        # apply SAUCE patches
        utils.system('patch -p1 < %s/001-fix-fallocate-test-before-kernel-4.3.patch' % self.bindir)

        # build for the underlying arch only (i.e. only 64 bit on 64 bit etc)
        utils.make('BUILDTYPE=NATIVEONLY')
        os.chdir(self.srcdir)

    def run_once(self):
        os.chdir(os.path.join(self.srcdir, 'libhugetlbfs'))
        self.results = utils.system_output('BUILDTYPE=NATIVEONLY make check', retain_output=True)

        print(self.results)

        n = self.results.find('FAIL:')
        if n > 0:
            m = self.results[n:].find('\n')
            if m > 0:
                fails = sum([int(s) for s in self.results[n:n + m].split() if s.isdigit()])
                if fails > 0:
                    raise error.TestError(str(fails) + ' test(s) failed.')

    def cleanup(self):
        if self.hugetlbfs_dir:
            utils.system('umount %s' % self.hugetlbfs_dir)
