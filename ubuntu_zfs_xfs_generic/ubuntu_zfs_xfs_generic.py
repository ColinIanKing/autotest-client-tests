#
#
import os
import platform
from autotest.client                        import test, utils
import platform

class ubuntu_zfs_xfs_generic(test.test):
    version = 2

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'acl',
            'attr',
            'autoconf',
            'automake',
            'autopoint',
            'bc',
            'build-essential',
            'dbench',
            'dump',
            'e2fsprogs',
            'fio',
            'gawk',
            'gdb',
            'gettext',
            'git',
            'kpartx',
            'ksh',
            'libtool',
            'libtool-bin',
            'pax',
            'pkg-config',
            'texinfo',
            'texlive',
            'quota'
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        if series in ['precise', 'trusty', 'utopic']:
            utils.system_output('add-apt-repository ppa:zfs-native/stable -y', retain_output=True)
            utils.system_output('apt-get update || true', retain_output=True)
            pkgs.append('ubuntu-zfs')
        elif series == 'wily':
            pkgs.append('zfs-dkms')
            pkgs.append('zfsutils-linux')
        else:
            pkgs.append('zfsutils-linux')

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()
        self.job.require_gcc()

    # if you change setup, be sure to increment version
    #
    def setup(self):
        utils.system_output('rm /etc/*/S99autotest || true', retain_output=True)

        utils.system_output('useradd fsgqa || true', retain_output=True)
        utils.system_output('echo \"fsgqa    ALL=(ALL)NOPASSWD: ALL\" >> /etc/sudoers', retain_output=True)
        print "Extracting xfstests.tar.bz2 tarball.."
        tarball = utils.unmap_url(self.bindir, 'xfstests-bld.tar.bz2', self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)

        os.chdir(os.path.join(self.srcdir, 'xfstests-dev'))
        print "Patching xfstests tarball.."
        utils.system('patch -p1 < %s/0001-xfstests-add-minimal-support-for-zfs.patch' % self.bindir)
        os.chdir(self.srcdir)

        print "Building xfstests"
        utils.system('make')
        utils.system('modprobe zfs')


    def run_once(self, test_name):
        #
        #  We need to call setup first to trigger setup() being
        #  invoked, then we can run run_once per test
        #
        if test_name == 'setup':
                return

        #os.chdir(self.srcdir)
	#print "chdir to " + os.path.join(self.srcdir, 'xfstests-dev')
	os.chdir(os.path.join(self.srcdir, 'xfstests-dev'))
        cmd = '%s/ubuntu_zfs_xfs_generic.sh %s %s' % (self.bindir, test_name, self.srcdir)
        print "Running: " + cmd
        self.results = utils.system_output(cmd, retain_output=True)
        print self.results
        print "Done!"

# vi:set ts=4 sw=4 expandtab syntax=python:
