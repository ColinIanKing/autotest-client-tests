import multiprocessing
import os, re, glob, logging
import platform
from autotest.client.shared import error
from autotest.client import test, utils, os_dep

class ubuntu_xfstests_xfs(test.test):

    version = 1

    PASSED_RE = re.compile(r'Passed all \d+ tests')
    FAILED_RE = re.compile(r'Failed \d+ of \d+ tests')
    NA_RE = re.compile(r'Passed all 0 tests')
    NA_DETAIL_RE = re.compile(r'(\d{3})\s*(\[not run\])\s*(.*)')
    GROUP_TEST_LINE_RE = re.compile('(\d{3})\s(.*)')

    def _get_available_tests(self):
        tests = glob.glob('???.out')
        tests += glob.glob('???.out.linux')
        tests = [t.replace('.linux', '') for t in tests]
        tests_list = [t[:-4] for t in tests if os.path.exists(t[:-4])]
        tests_list.sort()
        return tests_list

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'acl',
            'build-essential',
            'dump',
            'fio',
            'xfsdump',
            'autoconf',
            'keyutils',
            'kpartx',
            'thin-provisioning-tools',
            'libtool',
            'python-xattr',
            'quota',
            'bc',
            'attr',
            'texinfo',
            'texlive',
            'gettext',
            'git',
            'autopoint',
            'pkg-config',
            'libblkid-dev',
            'xfslibs-dev',
            'libattr1-dev',
            'libacl1-dev',
            'libaio-dev',
            'libssl-dev'
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        if series not in ['precise', 'trusty']:
            pkgs.append('libtool-bin')
        if series in ['xenial', 'bionic', 'disco']:
            pkgs.append('btrfs-tools')

        cmd = 'apt-get install --yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def _run_sub_test(self, test):
        os.chdir(os.path.join(self.srcdir, 'xfstests-bld', 'xfstests-dev'))
        output = utils.system_output('./check %s' % test,
                                     ignore_status=True,
                                     retain_output=True)
        lines = output.split('\n')
        result_line = lines[-1]

        if self.NA_RE.match(result_line):
            detail_line = lines[-3]
            match = self.NA_DETAIL_RE.match(detail_line)
            if match is not None:
                error_msg = match.groups()[2]
            else:
                error_msg = 'Test dependency failed, test not run'
            raise error.TestNAError(error_msg)

        elif self.FAILED_RE.match(result_line):
            raise error.TestError('Test error, check debug logs for complete '
                                  'test output')

        elif self.PASSED_RE.match(result_line):
            return

        else:
            raise error.TestError('Could not assert test success or failure, '
                                  'assuming failure. Please check debug logs')

    def _get_groups(self):
        '''
        Returns the list of groups known to xfstests

        By reading the group file and identifying unique mentions of groups
        '''
        groups = []
        for l in open(os.path.join(self.srcdir, 'group')).readlines():
            m = self.GROUP_TEST_LINE_RE.match(l)
            if m is not None:
                groups = m.groups()[1].split()
                for g in groups:
                    if g not in groups:
                        groups.add(g)
        return groups


    def _get_tests_for_group(self, group):
        '''
        Returns the list of tests that belong to a certain test group
        '''
        tests = []
        for l in open(os.path.join(self.srcdir, 'group')).readlines():
            m = self.GROUP_TEST_LINE_RE.match(l)
            if m is not None:
                test = m.groups()[0]
                groups = m.groups()[1]
                if group in groups.split():
                    if test not in tests:
                        tests.append(test)
        return tests


    def _run_suite(self):
        os.chdir(os.path.join(self.srcdir, 'xfstests-bld', 'xfstests-dev'))
        output = utils.system_output('./check -g auto -x dangerous',
                                     ignore_status=True,
                                     retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        '''
        Sets up the environment necessary for running xfstests
        '''
        self.install_required_pkgs()

        utils.system_output('useradd fsgqa || true', retain_output=True)
        utils.system_output('grep -q fsgqa /etc/sudoers || echo \"fsgqa    ALL=(ALL)NOPASSWD: ALL\" >> /etc/sudoers', retain_output=True)

        #
        # Anticipate failures due to missing devel tools, libraries, headers
        # and xfs commands
        #
        os_dep.command('autoconf')
        os_dep.command('autoheader')
        os_dep.command('libtool')
        os_dep.library('libuuid.so.1')
        #os_dep.header('xfs/xfs.h')
        #os_dep.header('attr/xattr.h')
        #os_dep.header('sys/acl.h')
        os_dep.command('mkfs.xfs')
        os_dep.command('xfs_db')
        os_dep.command('xfs_bmap')
        os_dep.command('xfsdump')

        self.job.require_gcc()

        # Hacky way to use proxy settings, ideally this should be done on deployment stage
        #
        print "Setup the http/https proxy"
        proxysets = [{'addr': 'squid.internal', 'desc': 'Running in the Canonical CI environment'},
                  {'addr': '91.189.89.216', 'desc': 'Running in the Canonical enablement environment'},
                  {'addr': '10.245.64.1', 'desc': 'Running in the Canonical enablement environment'}]
        for proxy in proxysets:
            cmd = 'nc -w 2 ' + proxy['addr'] + ' 3128'
            try:
                utils.system_output(cmd, retain_output=False)
                print proxy['desc']
                os.environ['http_proxy'] = 'http://' + proxy['addr'] + ':3128'
                os.environ['https_proxy'] = 'http://' + proxy['addr'] + ':3128'
                break
            except:
                pass

        print "Fetching xfstests.."
        os.chdir(self.srcdir)
        utils.system('git clone https://github.com/tytso/xfstests-bld')
        os.chdir(os.path.join(self.srcdir, 'xfstests-bld'))
        commit_bld = 'a4df7d7b31125901cb1fe9b092f495b6aa950448'
        print "Using head commit for xfstests-bld" + commit_bld
        utils.system('git reset --hard ' + commit_bld)
        # print "Patching xfstests-bld to add ARM64 xattr syscall support"
        # utils.system('patch -p1 < %s/0004-Add-syscalls-for-ARM64-platforms-LP-1755499.patch' % self.bindir)
        #
        #  Fix build link issues with newer toolchains (this is an ugly hack)
        #
        if float(platform.linux_distribution()[1]) > 18.04:
            print "Patching xfstest-blkd to fix static linking issue"
            utils.system('patch -p1 < %s/0005-build-all-remove-static-linking-flags-to-fix-build-i.patch' % self.bindir)
        print "Fetching all repos.."
        utils.system('./get-all')
        commit = "82eda8820ddd68dab0bc35199a53a08f58b1d26c"
        print "Using xfs from known stable commit point " + commit
        os.chdir('xfstests-dev')
        utils.system('git reset --hard ' + commit)
        print "Patching xfstests.."
        os.chdir(os.path.join(self.srcdir, 'xfstests-bld'))
        print "Building xfstests"
        utils.system('pwd')
        try:
            nprocs = '-j' + str(multiprocessing.cpu_count())
        except:
            nprocs = ''
        utils.make(nprocs)

        logging.debug("Available tests in srcdir: %s" %
                      ", ".join(self._get_available_tests()))

    def create_partitions(self, filesystem):
        print('/bin/bash %s/create-test-partitions %s %s' % (self.bindir, os.environ['XFSTESTS_TEST_DRIVE'], filesystem))
        return utils.system('/bin/bash %s/create-test-partitions %s %s' % (self.bindir, os.environ['XFSTESTS_TEST_DRIVE'], filesystem))

    def unmount_partitions(self):
        for mnt_point in [ os.environ['SCRATCH_MNT'], os.environ['TEST_DIR'] ]:
            utils.system('umount %s' % mnt_point, ignore_status=True)

    def run_once(self, test_name, filesystem='ext4', test_number='000', single=False, skip_dangerous=True):
        if test_name == 'setup':
            return

        os.chdir(self.srcdir)
        if single:
            if test_number == '000':
                self.unmount_partitions()
                self.create_partitions(filesystem)
                logging.debug('Dummy test to setup xfstests')
                return

            if test_number not in self._get_available_tests():
                raise error.TestError('test file %s not found' % test_number)

            if skip_dangerous:
                if test_number in self._get_tests_for_group('dangerous'):
                    raise error.TestNAError('test is dangerous, skipped')

            logging.debug("Running test: %s" % test_number)
            self._run_sub_test(test_number)

        else:
            self.create_partitions(filesystem)
            self._run_suite()
            self.unmount_partitions()
