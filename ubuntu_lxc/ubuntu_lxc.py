#
#
from autotest.client                        import test, utils
import os
import platform

class ubuntu_lxc(test.test):
    version = 1

    def install_required_pkgs(self):
        arch  = platform.processor()
        if self.series in ['precise', 'trusty', 'xenial', 'artful']:
            pkgs = [
                'lxc-tests'
            ]
        else:
            pkgs = [
                'automake',
                'autopkgtest',
                'build-essential',
                'cloud-image-utils',
                'dh-autoreconf',
                'lxc',
                'texinfo',
            ]
            gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
            pkgs.append(gcc)

        pkgs.append('liblxc1')
        cmd = 'apt-get install --yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.series = platform.dist()[2]
        pass

    def setup(self):
        self.install_required_pkgs()

    def run_once(self, test_name):
        if self.series in ['precise', 'trusty', 'xenial', 'artful']:
            cmd = '/bin/sh %s/exercise' % self.bindir
        else:
            proxy = ''
            if os.environ.get('http_proxy'):
                proxy = 'http_proxy=%s' % os.environ.get('http_proxy')
            cmd = '%s autopkgtest lxc -- null' % proxy

        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
