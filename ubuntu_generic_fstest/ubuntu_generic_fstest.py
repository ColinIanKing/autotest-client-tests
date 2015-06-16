#
#
import os
import glob
from autotest.client                        import test, utils
import multiprocessing
from autotest.client.shared import error

class ubuntu_generic_fstest(test.test):
    version = 1

    def initialize(self):
        self.job.require_gcc()


    #
    # if you change setup, be sure to increment version
    #
    def setup(self):
	utils.system_output('rm /etc/*/S99autotest || true', retain_output=True)

	pkgs = [ 'btrfs-tools', 'xfsprogs', 'jfsutils', 'hfsprogs' ]
	for pkg in pkgs:
		print "Installing package " + pkg
		utils.system_output('apt-get install ' + pkg + ' --yes --force-yes', retain_output=True)

	print "Extracting fstest tarball.."
	tarball = utils.unmap_url(self.bindir, 'fstest.tar.bz2', self.tmpdir)
	utils.extract_tarball_to_dir(tarball, self.srcdir)

	os.chdir(self.srcdir)
	print "Building fstest.."
        utils.system('make')

    def run_once(self, test_name):
	#
	#  We need to call setup first to trigger setup() being
	#  invoked, then we can run run_once per test
	#
	if test_name == 'setup':
		return

	mkfs = {
		'ext2' : 'mkfs.ext2 -F',
		'ext3' : 'mkfs.ext3 -F',
		'ext4' : 'mkfs.ext4 -F',
		'btrfs' : 'mkfs.btrfs -f',
		'xfs' : 'mkfs.xfs -f',
		'jfs' : 'mkfs.jfs -f' }

	mkfs_cmd = 'mkfs'
	if test_name in mkfs:
		mkfs_cmd = mkfs[test_name]

	os.chdir(self.srcdir)
	utils.system('truncate -s 128M /tmp/fstest.img')
	utils.system('losetup --find --show /tmp/fstest.img > loopname.tmp')
	utils.system('rm /tmp/fstest.img')
        loopdev = ''
	with open('loopname.tmp', 'r') as f:
		lines = f.readlines()
		loopdev = lines[0].rstrip('\n')

	print "Testing file system " + test_name
	utils.system('cat loopname.tmp')
	utils.system(mkfs_cmd + ' ' + loopdev)
	utils.system('mkdir -p /mnt/fstest')
	utils.system('mount ' + loopdev + ' /mnt/fstest')
	os.chdir('/mnt/fstest')

        cmd = 'prove --nocolor -q -r %s' % self.srcdir
	print "Running: " + cmd
        self.results = utils.system_output(cmd, retain_output=True, ignore_status=True)
        print self.results

	os.chdir(self.srcdir)
	utils.system('umount ' + loopdev)
	utils.system('losetup -d ' + loopdev)
	utils.system('rm -rf /mnt/fstest')
	utils.system('losetup -l')

	# parse output and raise test failure if 'prove' failed
	if self.results.find('Result: FAIL') != -1:
		raise error.TestFail('prove failed for ' + test_name)

# vi:set ts=4 sw=4 expandtab syntax=python:
