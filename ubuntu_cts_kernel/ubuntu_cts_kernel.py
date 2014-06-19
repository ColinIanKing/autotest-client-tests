from autotest.client                        import test,utils
from autotest.client.shared                 import error, software_manager

BUGS=['lp1256988','lp1153769','lp1262692','lp1026116']
DEPENDENCIES=['openvswitch-switch', 'iproute2', 'linux-tools-`uname -r`', 'coreutils', 'apparmor']

class ubuntu_cts_kernel(test.test):
    version = 1

    def initialize(self):
        pass

    def run_once(self, exit_on_error=True, set_time=True):
        for bug in BUGS:
            print('*** %s ***' % bug)
            cmd = '%s/bugs/%s' % (self.bindir, bug)
            self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
