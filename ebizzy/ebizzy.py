import os
import platform
from autotest.client import utils, test


class ebizzy(test.test):
    version = 4

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

    # http://sourceforge.net/project/downloading.php?group_id=202378&filename=ebizzy-0.3.tar.gz
    def setup(self, tarball='ebizzy-0.3.tar.gz'):
        self.install_required_pkgs()
        self.job.require_gcc()
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)

        utils.system('patch -p1 < %s/ebizzy-configure.patch' % self.bindir)
        utils.system('[ -x configure ] && ./configure')
        utils.make()

    # Note: default we use always mmap()
    def run_once(self, args='', num_chunks=1000, chunk_size=512000,
                 seconds=100, num_threads=100):

        # TODO: Write small functions which will choose many of the above
        # variables dynamicaly looking at guest's total resources
        logfile = os.path.join(self.resultsdir, 'ebizzy.log')
        args = '-m -n %s -P -R -s %s -S %s -t %s' % (num_chunks, chunk_size, seconds, num_threads)
        cmd = os.path.join(self.srcdir, 'ebizzy') + ' ' + args
        self.results = utils.system_output(cmd, retain_output=True)
