#
#
import multiprocessing
import os
import platform
import time
import yaml
from autotest.client                        import test, utils
from autotest.client.shared     import error

class ubuntu_ltp_syscalls(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()

        pkgs = [
            'automake',
            'bison',
            'build-essential',
            'byacc',
            'flex',
            'git',
            'libacl1-dev',
            'libaio-dev',
            'libcap-dev',
            'libmm-dev',
            'libnuma-dev',
            'libsctp-dev',
            'libselinux1-dev',
            'libssl-dev',
            'libtirpc-dev',
            'quota',
            'virt-what',
            'xfslibs-dev',
            'xfsprogs',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        if self.flavour in ['aws', 'azure', 'gcp', 'gke']:
            if not (self.flavour == 'aws' and self.series == 'trusty'):
                pkgs.append('linux-modules-extra-' + self.flavour + '*')
        if self.flavour not in ['kvm']:
            pkgs.append('nfs-kernel-server')
        if self.series not in ['trusty']:
            pkgs.append('haveged')
            pkgs.append('python-packaging')

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.series = platform.dist()[2]
        self.flavour = platform.uname()[2].split('-')[-1]
        self.kernel = platform.uname()[2].split('-')[0]
        pass

    # setup
    #
    #    Automatically run when there is no autotest/client/tmp/<test-suite> directory
    #
    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        os.chdir(self.srcdir)
        cmd = 'git clone --depth=1 https://github.com/linux-test-project/ltp.git'
        self.results = utils.system_output(cmd, retain_output=True)

        # Print test suite HEAD SHA1 commit id for future reference
        os.chdir(os.path.join(self.srcdir, 'ltp'))
        sha1 = utils.system_output('git rev-parse --short HEAD', retain_output=False, verbose=False)
        print("Test suite HEAD SHA1: {}".format(sha1))

        print("Patching utimensat_tests for Xenial...")
        utils.system('patch -N -p1 < %s/0001-utimensat_tests-fix-for-xenial.patch' % self.bindir)
        print("Patching fanotify09 for older kernels...")
        utils.system('patch -N -p1 < %s/0001-UBUNTU-SAUCE-skip-fanotify09-test-2-for-older-kernel.patch' % self.bindir)

        # Disable NTFS as we disable RW support
        cmd = 'sed -i /ntfs/d lib/tst_supported_fs_types.c'
        utils.system_output(cmd)

        utils.make('autotools')
        utils.configure()
        try:
            nprocs = '-j' + str(multiprocessing.cpu_count())
        except:
            nprocs = ''
        utils.make(nprocs)
        utils.make('install')

    def testcase_blacklist(self):
        try:
            from packaging.version          import parse
        except ImportError:
            # Compatibility fix for release < xenial
            from distutils.version import StrictVersion
        _blacklist = []
        fn = os.path.join(self.bindir, 'testcase-blacklist.yaml')
        with open(fn, 'r') as f:
            db = yaml.load(f)
        if self.flavour in db['flavour']:
            _blacklist += list(db['flavour'][self.flavour].keys())
        if self.flavour + '-' + self.series in db['flavour-series']:
            _blacklist += list(db['flavour-series'][self.flavour + '-' + self.series].keys())
        try:
            current_version = parse(self.kernel)
            for _kernel in db['kernel']:
                if current_version < parse(_kernel):
                    _blacklist += list(db['kernel'][_kernel].keys())
        except NameError:
            for _kernel in db['kernel']:
                if StrictVersion(self.kernel) < StrictVersion(_kernel):
                    _blacklist += list(db['kernel'][_kernel].keys())

        return _blacklist

    def should_stop_timesyncd(self, test):
        # trusty does not have systemd-timesyncd
        return test in ['leapsec01','stime01','settimeofday01','clock_settime'] and self.series != 'trusty'

    # run_once
    #
    #    Driven by the control file for each individual test.
    #
    def run_once(self, test_name):
        if test_name == 'setup':
            return
        fn = '/tmp/syscalls-' + time.strftime("%h%d-%H%M")
        log_failed = fn + '.failed'
        log_output = fn + '.output'

        fn = '/opt/ltp/runtest/%s' % (test_name)
        blacklisted = self.testcase_blacklist()

        print("Checking virt-what to see if we need to set LTP_TIMEOUT_MUL for getrandom02...")
        LTP_TIMEOUT_MUL = 1
        if utils.system_output('virt-what', verbose=False):
            print("Running in VM, set timeout multiplier LTP_TIMEOUT_MUL>1 (lp:1797327) for getrandom02")
            LTP_TIMEOUT_MUL = 3
        with open(fn , 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if blacklisted and line.strip() in blacklisted:
                        continue
                    with open ('/tmp/target' , 'w') as t:
                        t.write(line)

                    # Set the timeout multiplier exclusively for getrandom02 (lp:1831235)
                    if 'getrandom02' in line and LTP_TIMEOUT_MUL > 1:
                        os.environ["LTP_TIMEOUT_MUL"] = str(LTP_TIMEOUT_MUL)

                    # Stop timesyncd when testing time change
                    if self.should_stop_timesyncd(line):
                        utils.run('systemctl stop systemd-timesyncd')

                    cmd = '/opt/ltp/runltp -f /tmp/target -C %s -q -l %s -o %s -T /dev/null' % (log_failed, log_output, log_output)
                    utils.run(cmd, ignore_status=True, verbose=False)
                    # /dev/loop# creation will be taken care by the runltp

                    # Stop timesyncd when testing time change. Restart it now that it's done.
                    if self.should_stop_timesyncd(line):
                        utils.run('systemctl start systemd-timesyncd')

                    # Restore the timeout multiplier
                    if 'getrandom02' in line and 'LTP_TIMEOUT_MUL' in os.environ:
                        del os.environ["LTP_TIMEOUT_MUL"]

        num_failed = sum(1 for line in open(log_failed))
        num_blacklisted = len(blacklisted) if blacklisted else 0
        print("== Test Suite Summary ==")
        print("{} test cases failed").format(num_failed)
        print("{} test cases blacklisted").format(num_blacklisted)

        if num_failed > 0:
            cmd = "awk '{print$1}' " + log_failed + " | sort | uniq | tr '\n' ' '"
            failed_list = utils.system_output(cmd, retain_output=False, verbose=False)
            print("Failed test cases : %s" % failed_list)

        if num_blacklisted > 0:
            print("Blacklisted test cases: %s" % ', '.join(blacklisted))
        cmd = 'cat ' + log_output
        utils.system_output(cmd, retain_output=True, verbose=False)

        if num_failed > 0:
            raise error.TestFail()

# vi:set ts=4 sw=4 expandtab syntax=python:
