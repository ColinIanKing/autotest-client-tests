import os
from autotest.client import test, utils
import time

class ubuntu_fs_fio_perf(test.test):
    version = 1

    def initialize(self):
        self.job.require_gcc()
	self.valid_clients = ['gonzo', 'intel-uefi']
	self.hostname = os.uname()[1]
        if self.hostname == 'gonzo':
            self.dev = '/dev/sdb'
        elif self.hostname == 'intel-uefi':
            # cking's test box
            self.dev = '/dev/sda'
        else:
            self.dev = ''

    def setup(self):
        #
        # make the tools
        #
        tools = 'git-core fio xfsprogs btrfs-tools libaio-dev'

        #
        # totally abusing things, but this works for me :-)
        #
        utils.system('sudo apt-get -y -q install ' + tools)
        os.chdir(self.srcdir)
        utils.system('rm -rf fs-test-proto')
        utils.system('git clone git://kernel.ubuntu.com/cking/fs-test-proto.git')
        os.chdir(os.path.join(os.path.join(self.srcdir, 'fs-test-proto'), 'fio-tests'))
        utils.system('tar xvfz ../tools/fio-2.1.9.tar.gz')
        os.chdir(os.path.join(os.path.join(os.path.join(self.srcdir, 'fs-test-proto'), 'fio-tests'), 'fio'))
        utils.system('make clean')
        utils.system('make -j 4')
        os.chdir(self.srcdir)

        #
        #  Nuke any existing parition info and setup partition
        #
        utils.system('sudo dd if=/dev/zero of=' + self.dev + ' bs=1M count=256 > /dev/null 2>&1')
        utils.system('sudo parted ' + self.dev + ' mklabel gpt')
        utils.system('sudo parted -a optimal ' + self.dev + ' mkpart primary 0% 100%')
        utils.system('sudo parted ' + self.dev + ' print')

    def run_once(self, test_name):
        if test_name == 'setup':
            return
        #
        # We need to be sure we run this on the right target machines
        # as this is really quite destructive!
        #
        if not os.uname()[1] in self.valid_clients:
            return

        os.chdir(self.srcdir)
        date_start = time.strftime("%Y-%m-%d")
        time_start = time.strftime("%H%M")

        output = ''
        #
        # Test 3 different I/O schedulers:
        #
        for iosched in [ 'cfq', 'deadline', 'noop']:
            #
            # Test 5 different file systems, across 20+ tests..
            #
            os.chdir(os.path.join(os.path.join(self.srcdir, 'fs-test-proto'), 'fio-tests'))
            cmd = './test.sh'
            cmd += ' -d ' + self.dev + '1 -m 8G -S -s ' + iosched + ' -f ext2,ext3,ext4,xfs,btrfs'
            cmd += ' -D ' + date_start + ' -T ' + time_start
            output += utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab:
