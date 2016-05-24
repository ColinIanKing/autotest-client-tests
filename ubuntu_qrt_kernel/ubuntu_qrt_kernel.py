import os
import platform
from autotest.client import test, utils

class ubuntu_qrt_kernel(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential', 'libcap2-bin', 'gawk', 'execstack', 'exim4', 'libcap-dev',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_rquired_pkgs()
        self.job.require_gcc()

    def setup(self, tarball='ubuntu_qrt_kernel.tar.bz2'):
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        print(utils.system_output('head %s/scripts/bzr.log' % self.srcdir, retain_output=True))

        # For these tests we need to run as a non-root user. Part of the test is
        # compiling some test code and so the non-root user needs to be able to
        # create files in the tmp directory space.
        #
        self.results = utils.system_output('find %s -type d | xargs chmod 777' % self.srcdir, retain_output=True)

    def run_once(self, test_name):
        scripts = os.path.join(self.srcdir, 'scripts')
        os.chdir(scripts)

        if test_name == 'setup':
            return

        cmd = "sudo -u ubuntu python ./%s -v" % test_name
        self.results = utils.system_output(cmd, retain_output=True)


# vi:set ts=4 sw=4 expandtab:
