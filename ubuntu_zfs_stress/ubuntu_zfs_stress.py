#
#
import multiprocessing
import os
import platform
import shutil
from autotest.client                        import test, utils

class ubuntu_zfs_stress(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'build-essential',
            'gdb',
            'git',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        if series in ['precise', 'trusty']:
            utils.system_output('add-apt-repository ppa:zfs-native/stable -y', retain_output=True)
            utils.system_output('apt-get update || true', retain_output=True)
            pkgs.append('ubuntu-zfs')
        else:
            pkgs.append('zfsutils-linux')

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()

        utils.system('cp %s/ubuntu_zfs_stress.sh %s' % (self.bindir, self.srcdir))
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

        os.chdir(self.srcdir)
        utils.system_output('rm -f /etc/*/S99autotest || true', retain_output=True)
        utils.system('modprobe zfs')

    def run_once(self, test_name):
        stress_ng = os.path.join(self.srcdir, 'stress-ng', 'stress-ng')
        #
        #  temp logfile
        #
        log = '/tmp/zfs-falure.log'
        #
        #  stress-ng "quick fire" short life tests
        #
        dur = '5s'
        cmd = 'LOG=%s STRESS_NG=%s DURATION=%s bash -c %s/ubuntu_zfs_stress.sh %s 2>&1' % (log, stress_ng, dur, self.bindir, self.srcdir)
        self.results = utils.system_output(cmd, retain_output=True)
        #
        # FIXME: comment this out on production
        #
        #print(self.results)

# vi:set ts=4 sw=4 expandtab syntax=python:
