import multiprocessing
import os
import platform
from autotest.client import test, utils
import time

gb = 1024 * 1024 * 1024
mem_path = '/sys/devices/system/memory'

class ubuntu_fs_fio_perf(test.test):
    version = 1

    def online_all_memory(self):
        sys_memory = [ f for f in os.listdir(mem_path) if f.startswith("memory") ]
        for mem_file in sys_memory:
            try:
                with open(os.path.join(mem_path, mem_file, 'online'), 'w') as f:
                    f.write("1")
            except IOError:
                pass

    def online_shrink_memory(self, mem_required):
        sys_memory = sorted([ f for f in os.listdir(mem_path) if f.startswith("memory") ])
        with open(os.path.join(mem_path, 'block_size_bytes')) as f:
            mem_block_size = int(f.readline(), 16)

        online_blocks = 0
        online_memory = { }
        for mem_file in sys_memory:
            with open(os.path.join(mem_path, mem_file, 'online')) as f:
                online_memory[mem_file] = int(f.readline())
                online_blocks += online_memory[mem_file]

        mem_total = mem_block_size * online_blocks
        blocks_required = mem_required / mem_block_size

        if mem_total < mem_required:
            print("required %d GB but only have %d GB" % (mem_required / gb, mem_total / gb))
            return

        if mem_required < mem_block_size:
            print("required %d GB but minimum allowed is %d GB" % (mem_required / gb, mem_block_size / gb))
            mem_required = mem_block_size

        required_blocks = (mem_required + mem_block_size - 1) / mem_block_size
        if required_blocks < 1:
            required_blocks = 1
        blocks_to_offline = online_blocks - required_blocks

        print("%d x %d GB blocks online, %d blocks required, %d blocks to offline" % (online_blocks, mem_block_size / gb, required_blocks, blocks_to_offline))

        for mem_file in sys_memory:
            path = os.path.join(mem_path, mem_file, 'online')
            try:
                if online_memory[mem_file] == 1 and blocks_to_offline > 0:
                    with open(path, 'w') as f:
                        f.write("0")
            except IOError:
                pass

            with open(path, 'r') as f:
                if int(f.readline()) == 0:
                    blocks_to_offline -= 1

        online_blocks = 0
        for mem_file in sys_memory:
            path = os.path.join(mem_path, mem_file, 'online')
            with open(path) as f:
                online_blocks += int(f.readline())
        mem_total = mem_block_size * online_blocks
        print("memory online: %d GB" % (mem_total / gb))

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential',
            'git-core',
            'fio',
            'btrfs-progs',
            'libaio-dev',
            'git-core',
            'xfsdump',
            'xfsprogs',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.valid_clients = ['ivysaur']
        self.hostname = os.uname()[1]
        if self.hostname == 'ivysaur':
            self.dev = '/dev/sdb'
        else:
            raise error.TestError("ERROR: No device specified")
        self.fio_tests_dir = os.path.join(self.srcdir, 'fs-test-proto', 'fio-tests')

    def setup(self):
        # totally abusing things, but this works for me :-)
        #
        self.install_required_pkgs()
        self.job.require_gcc()

        os.chdir(self.srcdir)
        utils.system('rm -rf fs-test-proto')
        utils.system('git clone --depth=1 git://kernel.ubuntu.com/cking/fs-test-proto.git')
        # Print test suite HEAD SHA1 commit id for future reference
        os.chdir(os.path.join(self.srcdir, 'fs-test-proto'))
        sha1 = utils.system_output('git rev-parse --short HEAD', retain_output=False, verbose=False)
        print("Test suite HEAD SHA1: {}".format(sha1))

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
            print "unknown host"
            return

        date_start = time.strftime("%Y-%m-%d")
        time_start = time.strftime("%H%M")

        self.online_all_memory()
        self.online_shrink_memory(8 * gb)

        output = ''
        #
        # Test 3 different I/O schedulers:
        #
        devbase = os.path.basename(self.dev)
        with open(os.path.join('/sys/block', devbase, 'queue/scheduler')) as f:
            schedulers = f.readline().replace('[', '').replace(']', '').split()

        print("Using device %s (%s):" % (self.dev, devbase))
        print(schedulers)

        for iosched in schedulers:
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

        self.online_all_memory()

# vi:set ts=4 sw=4 expandtab:
