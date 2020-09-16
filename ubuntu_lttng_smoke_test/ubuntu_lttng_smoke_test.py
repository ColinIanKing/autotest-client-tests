#
#
import os
import platform
from autotest.client                        import test, utils
from autotest.client.shared                 import error

class ubuntu_lttng_smoke_test(test.test):
    version = 99

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'build-essential',
            'babeltrace',
            'lttng-tools',
            'lttng-modules-dkms',
            'liblttng-ust-dev',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        # Special case for Azure nodes lp: 1791032
        # Some nodes with small ram will need the swap to build lttng dkms
        if platform.uname()[2].split('-')[-1] == 'azure':
            mem_gb = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024.**3)
            df_gb = os.statvfs('/').f_bsize * os.statvfs('/').f_bavail / (1024.**3)
            cmd = 'swapon --show'
            swapon = utils.system_output(cmd)
            if mem_gb < 1.8 and df_gb > 4.0 and swapon == '':
                swap_file = '/tmp/swapfile'
                cmd = 'fallocate -l 2G %s' % swap_file
                utils.system(cmd)
                cmd = 'chmod 600 %s' % swap_file
                utils.system(cmd)
                cmd = 'mkswap %s' % swap_file
                utils.system(cmd)
                cmd = 'swapon %s' % swap_file
                utils.system(cmd)

        self.install_required_pkgs()
        self.job.require_gcc()
        cmd = 'dkms status -m lttng-modules | grep installed'
        try:
            utils.system(cmd)
        except error.CmdError:
            cmd = 'cat /var/lib/dkms/lttng-modules/*/build/make.log'
            utils.system(cmd)
            raise error.TestError('DKMS failed to install')

    def run_once(self, test_name):
        cmd = '%s/ubuntu_lttng_smoke_test.sh' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)
        print(self.results)

    def cleanup(self):
        cmd = 'apt-get remove --yes lttng-modules-dkms'
        self.results = utils.system_output(cmd, retain_output=False)

# vi:set ts=4 sw=4 expandtab syntax=python:
