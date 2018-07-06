import os
import platform
from autotest.client import test, utils


class isic(test.test):
    version = 2

    # http://www.packetfactory.net/Projects/ISIC/isic-0.06.tgz
    # + http://www.stardust.webpages.pl/files/crap/isic-gcc41-fix.patch

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.job.require_gcc()
        self.job.setup_dep(['libnet'])

    def setup(self, tarball='isic-0.06.tar.bz2'):
        self.install_required_pkgs()
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)

        utils.system('patch -p1 < %s/build-fixes.patch' % self.bindir)
        utils.system('patch -p1 < %s/isic-gcc5-fix.patch' % self.bindir)
        utils.system('PREFIX=%s/deps/libnet/libnet/ ./configure' % self.autodir)
        utils.system('make')

    def execute(self, args='-s rand -d 127.0.0.1 -p 10000000'):
        utils.system(self.srcdir + '/isic ' + args)
