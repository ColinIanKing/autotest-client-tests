#
#
import multiprocessing
import os
import platform
from autotest.client                        import test, utils

class ubuntu_zfs_fstest(test.test):
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
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64' ] else 'gcc-multilib'
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

    # if you change setup, be sure to increment version
    #
    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()

        print("Extracting fstest tarball..")
        tarball = utils.unmap_url(self.bindir, 'fstest.tar.bz2', self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)

        os.remove(self.srcdir + '/tests/chown/00.t')
        os.chdir(self.srcdir)
        print("Building fstest..")
        try:
            nprocs = '-j' + str(multiprocessing.cpu_count())
        except:
            nprocs = ''
        utils.make(nprocs)
        print("Loading zfs driver..")
        utils.system('modprobe zfs')

    def run_once(self, test_name):
        #
        #  We need to call setup first to trigger setup() being
        #  invoked, then we can run run_once per test
        #
        if test_name == 'setup':
                return

        os.chdir(self.srcdir)
        tmp_pool = os.path.join(self.srcdir, 'pool.img')
        utils.system('truncate -s 128M ' + tmp_pool)
        utils.system('zpool create pool ' + tmp_pool)
        utils.system('zfs create pool/test')
        os.chdir('/pool/test')

        cmd = 'prove --nocolor -q -r %s' % self.srcdir
        print("Running: " + cmd)
        self.results = utils.system_output(cmd, retain_output=True)
        print(self.results)
        os.chdir(self.srcdir)
        utils.system('zfs destroy pool/test')
        utils.system('zpool destroy pool')
        utils.system('dd if=/dev/zero of=' + tmp_pool + ' bs=1M count=128 >& /dev/null')
        utils.system('rm -f ' + tmp_pool)
        print("Done!")

# vi:set ts=4 sw=4 expandtab syntax=python:
