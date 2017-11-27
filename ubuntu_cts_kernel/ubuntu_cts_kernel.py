import platform
from autotest.client                        import test, utils

class ubuntu_cts_kernel(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'coreutils', 'apparmor', 'iproute2', 'openvswitch-switch',
        ]
        pkgs.append('linux-tools-%s' % platform.uname()[2])

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()

    def run_once(self, bug, exit_on_error=True, set_time=True, ifname=None):
        print('*** %s ***' % bug)
        cmd = '%s/bugs/%s %s' % (self.bindir, bug, ifname)
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
