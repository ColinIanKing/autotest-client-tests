#
#
import os
import glob
from autotest.client                        import test, utils
import multiprocessing

class ubuntu_btrfs_kernel_fixes(test.test):
    version = 1001

    #
    #  from #  http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
    #
    def is_exe(self, fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    def which(self, program):
        fpath, fname = os.path.split(program)
        if fpath:
            if self.is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if self.is_exe(exe_file):
                    return exe_file

        return None

    def initialize(self):
        self.job.require_gcc()
        if self.which('sysbench') == None:
		utils.system_output('sudo apt-get install sysbench --yes --force-yes', retain_output=True)

    #
    # if you change setup, be sure to increment version
    #
    def setup(self):
	# print "test names in: " + (os.path.join(self.srcdir, 'tests.txt'))
	f = open(os.path.join(self.srcdir, 'tests.txt'), 'w')
	test_files = sorted(glob.glob(os.path.join(self.bindir, 'fixes', '*.sh')))
	for file in test_files:
		f.write(file + "\n")
	f.close()
	self.job.test_files = test_files

    def run_once(self, test_name):
	#
	#  We need to call setup first to trigger setup() being
	#  invoked, then we can run run_once per test
	#
	if test_name == 'setup':
		return

        #
        #  mount point for btrfs
        #
        mnt = '/tmp/mnt-btrfs'
        #
        #  temp logfile
        #
        log = '/tmp/btrfs-falure.log'
        #
	#
	#
        cmd = 'BINDIR=%s %s/ubuntu_btrfs_kernel_fixes.sh %s 2>&1' % (self.bindir, self.bindir, test_name)
        self.results = utils.system_output(cmd, retain_output=True)
        print self.results

# vi:set ts=4 sw=4 expandtab syntax=python:
