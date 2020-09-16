#
#
import os
from autotest.client                        import test, utils
from autotest.client.shared                 import git

class ubuntu_k8s_unit_tests(test.test):
    version = 1

    def install_required_pkgs(self):
        pkgs = [
            'build-essential',
            'golang',
        ]

        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    # setup
    #
    #    Automatically run when there is no autotest/client/tmp/<test-suite> directory
    #
    def setup(self):
        self.install_required_pkgs()
        cmd = 'go version | grep -oP "(\d+\.)+\d+"'
        version = utils.system_output(cmd, retain_output=True, verbose=False)
        br = 'refs/tags/v' + version
        git.get_repo('https://github.com/kubernetes/kubernetes.git', branch=br, lbranch=None)

    # run_once
    #
    #    Driven by the control file for each individual test.
    #
    def run_once(self, test_name):
        if test_name == 'setup':
            return

        os.chdir('/tmp/kubernetes.git')
        utils.make('clean')
        self.results = utils.make('test')

# vi:set ts=4 sw=4 expandtab syntax=python:
