#
#
import os
from autotest.client                        import test, utils

class ubuntu_cve2_kernel(test.test):
    version = 1

    def install_required_pkgs(self):
        pkgs = [
            'gcc', 'sudo', 'make',
        ]
        cmd = 'DEBIAN_FRONTEND=noninteractive sudo apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def build_source(self):
        cmd = "make"
        os.chdir(self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()
        self.build_source()

    def run_once(self):

        os.chdir(self.bindir)
        cmd = "make check"
        self.results = utils.system_output(cmd, retain_output=True)

        print(self.results)

# vi:set ts=4 sw=4 expandtab syntax=python:
