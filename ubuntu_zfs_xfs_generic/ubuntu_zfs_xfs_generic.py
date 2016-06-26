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
            'bc',
            'build-essential',
            'gdb',
            'git',
            'ksh',
            'autoconf',
            'acl',
            'dump',
            'kpartx',
            'pax',
            'nfs-kernel-server',
            'xfslibs-dev',
            'uuid-dev',
            'libtool',
            'e2fsprogs',
            'automake',
            'gcc',
            'libuuid1',
            'quota',
            'attr',
            'libattr1-dev',
            'libacl1-dev',
            'libaio-dev',
            'xfsprogs',
            'libgdbm-dev',
            'gawk',
            'fio',
            'dbench',
            'libtool-bin'
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        if series in ['precise', 'trusty']:
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
        tarball = utils.unmap_url(self.bindir, 'xfstests.tar.bz2', self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)

        os.chdir(self.srcdir)
        print "Patching xfstests tarball.."
        utils.system('patch -p1 < %s/0001-xfstests-add-minimal-support-for-zfs.patch' % self.bindir)
        utils.system('patch -p2 < %s/0002-Fix-build-warnings-and-errors-hit-with-Xenial-gcc-5.patch' % self.bindir)
        utils.system('patch -p1 < %s/0003-xfstests-strip-out-single-quotes-to-enable-fuzzier-m.patch' % self.bindir)

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
