#
#
import os
from autotest.client                        import test, utils
from autotest.client.shared                 import error
import platform

class ubuntu_zfs(test.test):
    version = 4

    def initialize(self):
        self.job.require_gcc()

    #
    # if you change setup, be sure to increment version
    #
    def setup(self):
        series = platform.dist()[2]

        utils.system_output('rm /etc/*/S99autotest || true', retain_output=True)

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
            'nfs-kernel-server'
        ]

        if series == 'xenial':
            pkgs.append('zfsutils-linux')
        elif series == 'wily':
            pkgs.append('zfs-dkms')
            pkgs.append('zfsutils-linux')
        else:
            utils.system_output('add-apt-repository ppa:zfs-native/stable -y', retain_output=True)
            utils.system_output('apt-get update || true', retain_output=True)
            pkgs.append('ubuntu-zfs')

        for pkg in pkgs:
                print "Installing package " + pkg
                utils.system_output('apt-get install ' + pkg + ' --yes --force-yes', retain_output=True)

        utils.system_output('useradd zfs-tests || true', retain_output=True)
        utils.system_output('echo \"zfs-tests    ALL=(ALL)NOPASSWD: ALL\" >> /etc/sudoers', retain_output=True)
        print "Extracting zfs-test tarball.."
        tarball = utils.unmap_url(self.bindir, 'zfs-tests.tar.bz2', self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        utils.system_output('rsync -arv %s/tests %s/' % (self.bindir, self.srcdir))

        os.chdir(self.srcdir)

        print "Patching zfs-test tarball.."
        utils.system('patch -p1 < %s/zfs-tweaks.patch' % self.bindir)

        print "Building zfs-test tarball.."
        utils.system('./autogen.sh')
        utils.configure('')
        utils.system('SRCDIR=%s make' % self.srcdir)
        utils.system('modprobe zfs')


    def run_once(self, test_name):
        if test_name == 'setup':
            return

        os.chdir(self.srcdir)
        cmd = 'RUNFILE="-c %s/linux.run" make test' % self.srcdir
        #cmd = 'LINUX=linux make test'
        print "Running: " + cmd
        self.results = utils.system_output(cmd, retain_output=True)

        # parse output and raise test failure if 'prove' failed
        if self.results.find('FAIL') != -1:
            raise error.TestFail('Test failed for ' + test_name)


# vi:set ts=4 sw=4 expandtab syntax=python: