#
#
import os
import glob
import platform
from autotest.client                        import test, utils

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

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential', 'xfsprogs', 'btrfs-tools', 'git', 'acl', 'libattr1-dev',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        if self.which('sysbench') is None:
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

        cmd = 'BINDIR=%s %s/ubuntu_btrfs_kernel_fixes.sh %s 2>&1' % (self.bindir, self.bindir, test_name)
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
