#
#
import os
from autotest.client                        import test, utils
import multiprocessing

class ubuntu_stress_btrfs(test.test):
    version = 1

    def initialize(self):
        self.job.require_gcc()

        self.valid_clients = ['gonzo', 'btrfs-scratch']
        self.hostname = os.uname()[1]
        if self.hostname in ['gonzo', 'modoc']:
            self.dev = '/dev/sdb'
        elif self.hostname == 'btrfs-scratch':
            # cking's scratch test VM server
            self.dev = '/dev/vdb1'
        else:
            self.dev = ''

    def setup(self):
        utils.system('cp %s/ubuntu_stress_btrfs.sh %s' % (self.bindir, self.srcdir))
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
        dur = '5s'
        cmd = 'DEV=%s MNT=%s LOG=%s STRESS_NG=%s DURATION=%s %s/ubuntu_stress_btrfs.sh 2>&1' % (dev, mnt, log, stress_ng, dur, self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)
        #
        #  stress-ng "long soak" tests
        #
        dur = '1m'
        cmd = 'DEV=%s MNT=%s LOG=%s STRESS_NG=%s DURATION=%s %s/ubuntu_stress_btrfs.sh 2>&1' % (dev, mnt, log, stress_ng, dur, self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)

        #print self.results

# vi:set ts=4 sw=4 expandtab syntax=python:
