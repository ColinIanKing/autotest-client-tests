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
            gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
            pkgs.append(gcc)

        pkgs.append('liblxc1')
        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        try:
            self.series = platform.dist()[2]
        except AttributeError:
            import distro
            self.series = distro.codename()
        pass

    def setup(self):
        self.install_required_pkgs()

    def run_once(self, test_name):
        if test_name == 'setup':
            return
        if self.series in ['precise', 'trusty', 'xenial', 'artful']:
            cmd = '/bin/sh %s/exercise' % self.bindir
        else:
            proxy = ''
            if os.environ.get('http_proxy'):
                proxy = 'http_proxy=%s' % os.environ.get('http_proxy')
            cmd = '%s autopkgtest lxc -- null' % proxy

        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
