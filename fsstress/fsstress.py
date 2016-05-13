import os
from autotest.client import test, utils


class fsstress(test.test):
    version = 1

    def initialize(self):
        self.job.require_gcc()

    # http://www.zip.com.au/~akpm/linux/patches/stuff/ext3-tools.tar.gz
    def setup(self, tarball='ext3-tools.tar.gz'):
        self.tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(self.tarball, self.srcdir)

	utils.system_output('apt-get install xfsprogs jfsutils --assume-yes', retain_output=True)

        os.chdir(self.srcdir)
        utils.system('patch -p1 < %s/fsstress-ltp.patch' % self.bindir)
        utils.system('patch -p1 < %s/makefile.patch' % self.bindir)
        utils.make('fsstress')

    def run_once(self, fs, testdir=None, extra_args='', nproc='1000', nops='1000'):
        if not testdir:
            testdir = self.tmpdir
        image = os.path.join(testdir, 'fs.img')
        mntpath = os.path.join(testdir, 'mnt')
	tmppath = os.path.join(mntpath, 'tmp')
        os.mkdir(mntpath)

        self.results = utils.system_output('truncate --size 1G ' + image, retain_output=True)
        if fs == 'xfs':
            self.results += utils.system_output('mkfs.xfs -f ' + image, retain_output=True)
            self.results += utils.system_output('mount -t xfs -o loop ' + image + ' ' + mntpath, retain_output=True)
        elif fs == 'ext2':
            self.results += utils.system_output('mkfs.ext2 ' + image, retain_output=True)
            self.results += utils.system_output('mount -t ext4 -o loop ' + image + ' ' + mntpath, retain_output=True)
        elif fs == 'ext3':
            self.results += utils.system_output('mkfs.ext3 ' + image, retain_output=True)
            self.results += utils.system_output('mount -t ext4 -o loop ' + image + ' ' + mntpath, retain_output=True)
        elif fs == 'ext4':
            self.results += utils.system_output('mkfs.ext4 ' + image, retain_output=True)
            self.results += utils.system_output('mount -t ext4 -o loop ' + image + ' ' + mntpath, retain_output=True)
        elif fs == 'jfs':
            self.results += utils.system_output('mkfs.jfs -f ' + image, retain_output=True)
            self.results += utils.system_output('mount -t jfs -o loop ' + image + ' ' + mntpath, retain_output=True)

        os.mkdir(tmppath)
	os.chdir(tmppath)
        args = '-d %s -p %s -n %s %s' % (tmppath, nproc, nops, extra_args)
        cmd = self.srcdir + '/fsstress ' + args
        utils.system_output(cmd, retain_output=True)
	os.chdir(self.tmpdir)
        self.results += utils.system_output('umount ' + mntpath, retain_output=True)
	print self.results
        os.rmdir(mntpath)
        os.remove(image)
