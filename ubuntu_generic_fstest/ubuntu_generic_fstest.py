#
#
import os
import glob
from autotest.client                        import test, utils
import multiprocessing
import platform
from autotest.client.shared import error

class ubuntu_generic_fstest(test.test):
    version = 1

    def initialize(self):
        pass


    #
    # if you change setup, be sure to increment version
    #
    def setup(self):
        series = platform.dist()[2]
        self.job.require_gcc()
        utils.system_output('rm -f /etc/*/S99autotest || true', retain_output=True)

        pkgs = [ 'xfsprogs', 'jfsutils' ]
        if series in ['precise', 'trusty', 'xenial']:
            pkgs.append('btrfs-tools')
        else:
            pkgs.append('btrfs-progs')
        for pkg in pkgs:
            print "Installing package " + pkg
            utils.system_output('apt-get install ' + pkg + ' --yes --force-yes ', retain_output=True)

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

        #
        #  mapping of file system to fstest characteristic type and mkfs rule
        #
        mkfs = {
                'ext2'  : [ 'ext3', 'mkfs.ext2 -F'],
                'ext3'  : [ 'ext3', 'mkfs.ext3 -F'],
                'ext4'  : [ 'ext3', 'mkfs.ext4 -F'],
                'btrfs' : [ 'ext3', 'mkfs.btrfs -f' ],
                'xfs'   : [ 'xfs',  'mkfs.xfs -f' ],
                'jfs'   : [ 'ext3', 'mkfs.jfs -f' ] }

        if test_name not in mkfs:
            print 'SKIPPING: file system ' + test_name + ' not known to test'
            return

        #
        #  some tests are known to fail across all kernels for some
        #  file systems, so add an exception list of tests to skip
        #
        skip_tests = {
                      'xfs' : [ 'tests/chown/00.t' ]
        }

        mkfs_cmd = 'mkfs'
        if test_name in mkfs:
            mkfs_cmd = mkfs[test_name][1]

        os.chdir(self.srcdir)
        utils.system('truncate -s 128M /tmp/fstest.img')
        utils.system('losetup --find --show /tmp/fstest.img > loopname.tmp')
        utils.system('rm -f /tmp/fstest.img')
        loopdev = ''
        with open('loopname.tmp', 'r') as f:
            lines = f.readlines()
            loopdev = lines[0].rstrip('\n')

        #
        # Gather sorted name of all tests
        #
        tests = sorted([os.path.join(r,f) for r,d,fs in os.walk('tests') for f in fs if f.endswith('.t')])

        print "Testing file system " + test_name + " on dev " + loopdev
        utils.system(mkfs_cmd + ' ' + loopdev)
        utils.system('mkdir -p /mnt/fstest')
        utils.system('mount ' + loopdev + ' /mnt/fstest')
        os.chdir('/mnt/fstest')

        #
        # We need to set up a configuration file per file system type
        #
        conf = open(os.path.join(self.srcdir, 'tests', 'conf'), 'w')
        conf.write('os=`uname`\n')
        conf.write('fs="%s"\n' % mkfs[test_name][0])
        conf.close()


        if test_name in skip_tests:
            skip = skip_tests[test_name]
        else:
            skip = []

        #
        # Run each test, unless it is to be skipped
        #
        failed =  ""
        for test in tests:
            print
            if test in skip:
                print test_name + ': ' + test + ': SKIPPED (tests known to have issues)'
            else:
                print test_name + ': ' + test + ':'
                cmd = 'prove --nocolor -q -r %s' % os.path.join(self.srcdir, test)
                self.results = utils.system_output(cmd, retain_output=True, ignore_status=True)
                print self.results

                # parse output and raise test failure if 'prove' failed
                if self.results.find('Result: FAIL') != -1:
                    failed = failed + ' ' + test

        print
        if failed != "":
            raise error.TestFail('Tests failed for ' + test + ' for file system ' + test_name)
        else:
            print 'Tests all passed for file system ' + test_name

        os.chdir(self.srcdir)
        utils.system('umount ' + loopdev)
        utils.system('losetup -d ' + loopdev)
        utils.system('rm -rf /mnt/fstest')
        utils.system('losetup -l')

# vi:set ts=4 sw=4 expandtab syntax=python:
