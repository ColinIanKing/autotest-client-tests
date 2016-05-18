#
#
import os
import platform
from autotest.client                        import test, utils
import platform

class ubuntu_zfs_fstest(test.test):
    version = 1

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
            'nfs-kernel-server',
            'xfsprogs',
            'libattr1-dev',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64'] else 'gcc-multilib'
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
        series = platform.dist()[2]

        print "Extracting fstest tarball.."
        tarball = utils.unmap_url(self.bindir, 'fstest.tar.bz2', self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)

        os.chdir(self.srcdir)
        print "Building fstest.."
        utils.system('make')
        print "Loading zfs driver.."
        utils.system('modprobe zfs')

    def run_once(self, test_name):
        #
        #  We need to call setup first to trigger setup() being
        #  invoked, then we can run run_once per test
        #
        if test_name == 'setup':
                return

        os.chdir(self.srcdir)
        utils.system('truncate -s 128M /tmp/pool.img')
        utils.system('zpool create pool /tmp/pool.img')
        utils.system('zfs create pool/test')
        os.chdir('/pool/test')

        cmd = 'prove --nocolor -q -r %s' % self.srcdir
        print "Running: " + cmd
        self.results = utils.system_output(cmd, retain_output=True)
        print self.results
        os.chdir(self.srcdir)
        utils.system('zfs destroy pool/test')
        utils.system('zpool destroy pool')
        utils.system('rm /tmp/pool.img')
        print "Done!"

# vi:set ts=4 sw=4 expandtab syntax=python:
