import os
import logging
from autotest.client import test, utils
import platform


class tiobench(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
       try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'build-essential', 'gnuplot', 'xfsdump', 'xfsprogs',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)
        if series in ['precise', 'trusty', 'xenial']:
            pkgs.append('btrfs-tools')
        else:
            pkgs.append('btrfs-progs')

        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    # http://prdownloads.sourceforge.net/tiobench/tiobench-0.3.3.tar.gz
    def setup(self, tarball='tiobench-0.3.3.tar.bz2'):
        self.install_required_pkgs()
        self.job.require_gcc()
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)
        utils.system('patch -p1 < %s/makefile.patch' % self.bindir)
        utils.system('patch -p1 < %s/tiotest.patch' % self.bindir)
        utils.system('make')

    def run_once(self, dir=None, args=None):
        if not dir:
            self.dir = self.tmpdir
        else:
            self.dir = dir
        if not args:
            self.args = '--block=4096 --block=8192 --threads=10 --size=1024 --numruns=2'
        else:
            self.args = args

        os.chdir(self.srcdir)
        results = utils.system_output('./tiobench.pl --dir %s %s' %
                                      (self.dir, self.args))

        logging.info(results)
        results_path = os.path.join(self.resultsdir,
                                    'raw_output_%s' % self.iteration)

        utils.open_write_close(results_path, results)
