from autotest.client                        import test,utils
from autotest.client.shared                 import error, software_manager

DEPENDENCIES=['openvswitch-switch', 'iproute2', 'linux-tools-`uname -r`', 'coreutils', 'apparmor']

class ubuntu_cts_kernel(test.test):
    version = 1

    def initialize(self):
        pass

    def run_once(self, bug, exit_on_error=True, set_time=True, ifname='eth0'):
        print('*** %s ***' % bug)
        cmd = '%s/bugs/%s %s' % (self.bindir, bug, ifname)
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
