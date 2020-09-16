#
#
from autotest.client                        import test, utils
import platform

class ubuntu_squashfs_smoke_test(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'xfsprogs', 'git', 'acl', 'libattr1-dev', 'squashfs-tools', 'bc',
        ]

        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()

    def run_once(self, test_name):
        cmd = '%s/ubuntu_squashfs_smoke_test.sh' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
