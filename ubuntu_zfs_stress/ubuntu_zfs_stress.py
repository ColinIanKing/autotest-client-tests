#
#
import os
from autotest.client                        import test, utils
import multiprocessing

class ubuntu_zfs_stress(test.test):
    version = 1

    def initialize(self):
        self.job.require_gcc()

    def setup(self):
        utils.system('cp %s/ubuntu_zfs_stress.sh %s' % (self.bindir, self.srcdir))
        os.chdir(self.srcdir)
        cmd = 'git clone git://kernel.ubuntu.com/cking/stress-ng 2>&1'
        self.results = utils.system_output(cmd, retain_output=True)

        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        cmd = 'make -j 4'
        self.results = utils.system_output(cmd, retain_output=True)

        cmd = 'ls -al ' + self.bindir
        self.results = utils.system_output(cmd, retain_output=True)

        os.chdir(self.srcdir)

        utils.system_output('rm /etc/*/S99autotest || true', retain_output=True)

        utils.system_output('add-apt-repository ppa:zfs-native/stable -y', retain_output=True)
        utils.system_output('apt-get update || true', retain_output=True)

        pkgs = ['build-essential', 'gdb', 'git', 'ksh', 'autoconf', 'build-essential',
                'ubuntu-zfs', 'acl', 'dump', 'kpartx', 'pax',
                'nfs-kernel-server' ]
        for pkg in pkgs:
                print "Installing package " + pkg
                utils.system_output('apt-get install ' + pkg + ' --yes --force-yes', retain_output=True)

        utils.system('modprobe zfs')


    def run_once(self, test_name):
        self.job.require_gcc()

        stress_ng = os.path.join(self.srcdir, 'stress-ng', 'stress-ng')
        #
        #  temp logfile
        #
        log = '/tmp/zfs-falure.log'
        #
        #  stress-ng "quick fire" short life tests
        #
        dur = '5s'
        cmd = 'LOG=%s STRESS_NG=%s DURATION=%s bash -c %s/ubuntu_zfs_stress.sh 2>&1' % (log, stress_ng, dur, self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)
        #
        # FIXME: comment this out on production
        #
        #print self.results

# vi:set ts=4 sw=4 expandtab syntax=python:
