#
#
import os
from autotest.client                        import test, utils
from autotest.client.shared                 import error
import platform

class ubuntu_zfs(test.test):
    version = 4

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
            'libattr1-dev'
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
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
        pass

    #
    # if you change setup, be sure to increment version
    #
    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()

        utils.system_output('rm -f /etc/*/S99autotest || true', retain_output=True)

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
