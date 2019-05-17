#
#
import multiprocessing
import os
import platform
from autotest.client                        import test, utils

class ubuntu_ramfs_stress(test.test):
    version = 0

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'perl',
            'build-essential',
            'gdb',
            'git',
            'ksh',
            'autoconf',
            'acl',
            'dump',
            'kpartx',
            'pax',
            'xfsprogs',
            'libattr1-dev',
            'libkeyutils-dev',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()

        utils.system('cp %s/ubuntu_ramfs_stress.sh %s' % (self.bindir, self.srcdir))
        os.chdir(self.srcdir)
        cmd = 'git clone --depth=1 git://kernel.ubuntu.com/cking/stress-ng 2>&1'
        self.results = utils.system_output(cmd, retain_output=True)

        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        try:
            nprocs = '-j' + str(multiprocessing.cpu_count())
        except:
            nprocs = ''
        utils.make(nprocs)

        cmd = 'ls -al ' + self.bindir
        self.results = utils.system_output(cmd, retain_output=True)

        os.chdir(self.srcdir)

        utils.system_output('rm -f /etc/*/S99autotest || true', retain_output=True)

    def run_once(self, test_name):
        if test_name == 'setup':
            return
        stress_ng = os.path.join(self.srcdir, 'stress-ng', 'stress-ng')
        #
        #  temp logfile
        #
        log = '/tmp/ramfs-falure.log'
        #
        #  stress-ng "quick fire" short life tests
        #
        dur = '30s'
        cmd = 'LOG=%s STRESS_NG=%s DURATION=%s bash -c %s/ubuntu_ramfs_stress.sh %s 2>&1' % (log, stress_ng, dur, self.bindir, self.srcdir)
        self.results = utils.system_output(cmd, retain_output=True)
        #
        # FIXME: comment this out on production
        #
        #print self.results

# vi:set ts=4 sw=4 expandtab syntax=python:
