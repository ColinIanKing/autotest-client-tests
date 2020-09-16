import platform
from autotest.client                        import test, utils

class ubuntu_cts_kernel(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()
        major_kernel_version = platform.uname()[2].split('-')[0]

        pkgs = [
            'coreutils', 'apparmor', 'openvswitch-switch', 'linux-tools-common',
        ]
        if series == 'precise':
            pkgs.append('iproute')
        else:
            pkgs.append('iproute2')

        if series not in ['precise', 'trusty']:
            pkgs.append('net-tools')

        if major_kernel_version == '3.2.0':
            pkgs.append('linux-tools')
        else:
            pkgs.append('linux-tools-%s' % platform.uname()[2])

        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()

    def run_once(self, bug, exit_on_error=True, set_time=True, ifname=None):
        print('*** %s ***' % bug)
        cmd = '%s/bugs/%s %s' % (self.bindir, bug, ifname)
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
