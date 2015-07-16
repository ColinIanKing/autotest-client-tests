#
#
import os
import glob
from autotest.client                        import test, utils
import multiprocessing

class ubuntu_zfs_xfs_generic(test.test):
    version = 2

    def initialize(self):
        self.job.require_gcc()


    #
    # if you change setup, be sure to increment version
    #
    def setup(self):
        utils.system_output('rm /etc/*/S99autotest || true', retain_output=True)

        utils.system_output('add-apt-repository ppa:zfs-native/stable -y', retain_output=True)
        utils.system_output('apt-get update || true', retain_output=True)

        pkgs = ['build-essential', 'gdb', 'git', 'ksh', 'autoconf', 'build-essential',
                'ubuntu-zfs', 'acl', 'dump', 'kpartx', 'pax',
                'nfs-kernel-server', 'xfslibs-dev', 'uuid-dev', 'libtool', 'e2fsprogs',
                'automake', 'gcc', 'libuuid1', 'quota', 'attr', 'libattr1-dev',
                'libacl1-dev', 'libaio-dev', 'xfsprogs',  'libgdbm-dev', 'gawk',
                'fio', 'dbench', 'libtool-bin' ]
        for pkg in pkgs:
                print "Installing package " + pkg
                utils.system_output('apt-get install ' + pkg + ' --yes --force-yes', retain_output=True)

        utils.system_output('useradd fsgqa || true', retain_output=True)
        utils.system_output('echo \"fsgqa    ALL=(ALL)NOPASSWD: ALL\" >> /etc/sudoers', retain_output=True)
        print "Extracting xfstests.tar.bz2 tarball.."
        tarball = utils.unmap_url(self.bindir, 'xfstests.tar.bz2', self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)

        os.chdir(self.srcdir)
        print "Patching xfstests tarball.."
        utils.system('patch -p1 < %s/0001-xfstests-add-minimal-support-for-zfs.patch' % self.bindir)
        print "Building xfstests tarball.."
        #utils.make()
        utils.system('make -j 8')
        utils.system('make install')
        utils.system('modprobe zfs')


    def run_once(self, test_name):
        #
        #  We need to call setup first to trigger setup() being
        #  invoked, then we can run run_once per test
        #
        if test_name == 'setup':
                return

        os.chdir(self.srcdir)
        cmd = '%s/ubuntu_zfs_xfs_generic.sh %s' % (self.bindir, test_name)
        print "Running: " + cmd
        self.results = utils.system_output(cmd, retain_output=True)
        print self.results
        print "Done!"

# vi:set ts=4 sw=4 expandtab syntax=python:
