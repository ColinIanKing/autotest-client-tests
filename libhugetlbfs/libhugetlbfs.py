import re
import os
from autotest.client import utils, test, os_dep
from autotest.client.shared import error


class libhugetlbfs(test.test):
    version = 7

    def initialize(self, hugetlbfs_dir=None, pages_requested=20):
        self.hugetlbfs_dir = None

        # check if basic utilities are present
        self.job.require_gcc()
        utils.check_kernel_ver("2.6.16")
        os_dep.library('libpthread.a')

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

    def setup(self, tarball='libhugetlbfs-2.14.tar.gz'):
        # get the sources
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)
        utils.system('patch -p1 < %s/elflink.patch' % self.bindir)
        utils.system('patch -p1 < %s/build-fixes.patch' % self.bindir)

        # build for the underlying arch only (i.e. only 64 bit on 64 bit etc)
        utils.make('BUILDTYPE=NATIVEONLY')

    def run_once(self):
        os.chdir(self.srcdir)
        self.results = utils.system_output('BUILDTYPE=NATIVEONLY make check', retain_output=True)

	print self.results

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
