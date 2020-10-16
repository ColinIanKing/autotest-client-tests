#
#
import multiprocessing
import os
from autotest.client                        import test, utils
import platform

class ubuntu_stress_smoke_test(test.test):
    version = 1

    def get_codename(self):
        try:
            for line in open('/etc/lsb-release').read().split('\n'):
                if line.startswith('DISTRIB_CODENAME='):
                    return line.split('=')[1].replace('"','')
            return 'unknown'
        except:
            return 'unknown'

    def install_required_pkgs(self):
        arch   = platform.processor()

        pkgs = [
            'apparmor',
            'build-essential',
            'git',
            'libaio-dev',
            'libapparmor-dev',
            'libattr1-dev',
            'libbsd-dev',
            'libkeyutils-dev',
            'zlib1g-dev',
        ]

        codename = self.get_codename()
        cgroup_tool = 'cgroup-bin' if codename in [ 'precise', 'trusty' ] else 'cgroup-tools'
        pkgs.append(cgroup_tool)

        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        os.chdir(self.srcdir)
        cmd = 'git clone --depth=1 git://kernel.ubuntu.com/cking/stress-ng'
        self.results = utils.system_output(cmd, retain_output=True)

        # Print test suite HEAD SHA1 commit id for future reference
        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        sha1 = utils.system_output('git rev-parse --short HEAD', retain_output=False, verbose=False)
        print("Test suite HEAD SHA1: {}".format(sha1))

        try:
            nprocs = '-j' + str(multiprocessing.cpu_count())
        except:
            nprocs = ''
        utils.make(nprocs)

    def run_once(self, test_name):
        if test_name == 'setup':
            return

        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        cmd = '%s/ubuntu_stress_smoke_test.sh' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)

        print(self.results)

# vi:set ts=4 sw=4 expandtab syntax=python:
