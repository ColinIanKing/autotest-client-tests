#
#
import os
import platform
from autotest.client                        import test, utils

class ubuntu_stress_btrfs_cmd(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential', 'xfsprogs', 'btrfs-tools', 'git', 'acl', 'libattr1-dev',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.job.require_gcc()

        self.valid_clients = ['gonzo', 'btrfs-scratch']
        self.hostname = os.uname()[1]
        if self.hostname == 'gonzo':
            self.dev = '/dev/sdb'
        elif self.hostname == 'btrfs-scratch':
            # cking's scratch test VM server
            self.dev = '/dev/vdb1'
        else:
            self.dev = 'loop'

    def setup(self):
        self.install_required_pkgs(self)

        utils.system('cp %s/ubuntu_stress_btrfs_cmd.sh %s' % (self.bindir, self.srcdir))
        os.chdir(self.srcdir)
        cmd = 'git clone git://kernel.ubuntu.com/cking/stress-ng 2>&1'
        self.results = utils.system_output(cmd, retain_output=True)

        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        cmd = 'make -j 4'
        self.results = utils.system_output(cmd, retain_output=True)

        cmd = 'ls -al ' + self.bindir
        self.results = utils.system_output(cmd, retain_output=True)

        os.chdir(self.srcdir)

    def run_once(self, test_name):
        self.job.require_gcc()

        stress_ng = os.path.join(self.srcdir, 'stress-ng', 'stress-ng')
        #
        #  device to use for btrfs
        #
        dev = self.dev
        #
        #  mount point for btrfs
        #
        mnt = '/tmp/mnt-btrfs'
        #
        #  temp logfile
        #
        log = '/tmp/btrfs-falure.log'
        #
        #  stress-ng "quick fire" short life tests
        #
        cmd = 'DEV=%s MNT=%s LOG=%s STRESS_NG=%s %s/ubuntu_stress_btrfs_cmd.sh 2>&1' % (dev, mnt, log, stress_ng, self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)

        #print self.results

# vi:set ts=4 sw=4 expandtab syntax=python:
