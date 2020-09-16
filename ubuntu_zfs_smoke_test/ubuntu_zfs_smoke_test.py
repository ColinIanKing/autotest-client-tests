#
#
from autotest.client                        import test, utils
import platform

class ubuntu_zfs_smoke_test(test.test):
    version = 3

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'xfsprogs', 'git', 'acl', 'libattr1-dev',
        ]

        if series in ['precise', 'trusty']:
            utils.system_output('add-apt-repository ppa:zfs-native/stable -y', retain_output=True)
            utils.system_output('apt-get update || true', retain_output=True)
            pkgs.append('ubuntu-zfs')
        elif series == 'wily':
            pkgs.append('zfs-dkms')
            pkgs.append('zfsutils-linux')
        else:
            pkgs.append('zfsutils-linux')

        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()
        utils.system('modprobe zfs')

    def run_once(self, test_name):
        if test_name == 'setup':
            return
        cmd = '%s/%s %s' % (self.bindir, test_name, self.srcdir)
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
