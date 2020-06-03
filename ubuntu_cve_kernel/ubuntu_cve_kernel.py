import platform
from autotest.client                        import test, utils

class ubuntu_cve_kernel(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential', 'git', 'libkeyutils-dev', 'libfuse-dev', 'pkg-config', 'expect', 'libecryptfs-dev', 'ecryptfs-utils'
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        utils.system('make -C %s/cves' % self.bindir)

    def run_once(self, cve, exit_on_error=True, set_time=True):
        print('*** %s ***' % cve)
        cmd = 'make -C %s/cves/%s check' % (self.bindir, cve)
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
