#
#
import multiprocessing
import os
import platform
import shutil
from autotest.client                        import test, utils

class ubuntu_stress_btrfs_cmd(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'build-essential', 'xfsprogs', 'git', 'acl', 'libattr1-dev',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)
        if series in ['precise', 'trusty', 'xenial']:
            pkgs.append('btrfs-tools')
        else:
            pkgs.append('btrfs-progs')

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
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
        self.install_required_pkgs()
        self.job.require_gcc()

        utils.system('cp %s/ubuntu_stress_btrfs_cmd.sh %s' % (self.bindir, self.srcdir))
        os.chdir(self.srcdir)
        shutil.rmtree('stress-ng', ignore_errors=True)
        cmd = 'git clone --depth=1 git://git.launchpad.net/~canonical-kernel-team/+git/stress-ng 2>&1'
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

        cmd = 'ls -al ' + self.bindir
        self.results = utils.system_output(cmd, retain_output=True)

        os.chdir(self.srcdir)

    def run_once(self, test_name):
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

        #print(self.results)

# vi:set ts=4 sw=4 expandtab syntax=python:
