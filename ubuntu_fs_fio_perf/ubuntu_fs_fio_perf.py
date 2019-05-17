import multiprocessing
import os
import platform
from autotest.client import test, utils
import time

class ubuntu_fs_fio_perf(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential',
            'git-core',
            'fio',
            'xfsprogs',
            'btrfs-tools',
            'libaio-dev',
            'git-core',
            'fio',
            'libaio-dev',
            'xfsdump',
            'xfsprogs',
            'btrfs-tools',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.valid_clients = ['gonzo', 'intel-uefi']
        self.hostname = os.uname()[1]
        if self.hostname == 'gonzo':
            self.dev = '/dev/sdb'
        elif self.hostname == 'intel-uefi':
            # cking's test box
            self.dev = '/dev/sda'
        else:
            self.dev = ''
        self.fio_tests_dir = os.path.join(self.srcdir, 'fs-test-proto', 'fio-tests')

    def setup(self):
        # totally abusing things, but this works for me :-)
        #
        self.install_required_pkgs()
        self.job.require_gcc()

        os.chdir(self.srcdir)
        utils.system('rm -rf fs-test-proto')
        utils.system('git clone --depth=1 git://kernel.ubuntu.com/cking/fs-test-proto.git')
        os.chdir(self.fio_tests_dir)
        utils.system('tar xvfz ../tools/fio-2.1.9.tar.gz')
        os.chdir(os.path.join(self.fio_tests_dir, 'fio'))
        utils.make('clean')
        try:
            nprocs = '-j' + str(multiprocessing.cpu_count())
        except:
            nprocs = ''
        utils.make(nprocs)
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

        date_start = time.strftime("%Y-%m-%d")
        time_start = time.strftime("%H%M")

        output = ''
        #
        # Test 3 different I/O schedulers:
        #
        for iosched in ['cfq', 'deadline', 'noop']:
            #
            # Test 5 different file systems, across 20+ tests..
            #
            os.chdir(self.fio_tests_dir)
            cmd = './test.sh'
            cmd += ' -d ' + self.dev + '1 -m 8G -S -s ' + iosched + ' -f ext2,ext3,ext4,xfs,btrfs'
            cmd += ' -D ' + date_start + ' -T ' + time_start
            output += utils.system_output(cmd, retain_output=True)

        #
        # Move the results from the src tree into the autotest results tree where it will automatically
        # get picked up and copied over to the jenkins server.
        #
        os.rename(os.path.join(self.srcdir, 'fs-test-proto'), os.path.join(self.resultsdir, 'fs-test-proto'))

# vi:set ts=4 sw=4 expandtab:
