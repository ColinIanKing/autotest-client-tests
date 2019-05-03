#
#
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
            'nfs-kernel-server',
            'quota',
            'virt-what',
            'xfslibs-dev',
            'xfsprogs',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        flavour = platform.uname()[2].split('-')[-1]
        if flavour in ['azure', 'gcp']:
             pkgs.append('linux-modules-extra-' + flavour + '*')

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
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

        os.chdir(os.path.join(self.srcdir, 'ltp'))
        print("Patching utimensat_tests for Xenial...")
        utils.system('patch -N -p1 < %s/0001-utimensat_tests-fix-for-xenial.patch' % self.bindir)
        cmd = 'make autotools'
        self.results = utils.system_output(cmd, retain_output=True)
        cmd = './configure'
        self.results = utils.system_output(cmd, retain_output=True)
        cmd = 'make'
        self.results = utils.system_output(cmd, retain_output=True)
        cmd = 'make install'
        self.results = utils.system_output(cmd, retain_output=True)

    def testcase_blacklist(self):
        flavour = platform.release().split('-')[2]
        fn = os.path.join(self.bindir, 'testcase-blacklist.yaml')
        with open(fn, 'r') as f:
            db = yaml.load(f)

        if flavour in db['flavour']:
            return list(db['flavour'][flavour].keys())

        return None

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

        print("Checking virt-what to see if we need to set LTP_TIMEOUT_MUL...")
        if utils.system_output('virt-what', verbose=False):
            print("Running in VM, set timeout multiplier LTP_TIMEOUT_MUL=3 (lp:1797327)")
            os.environ["LTP_TIMEOUT_MUL"] = "3"
        with open(fn , 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if blacklisted and line.strip() in blacklisted:
                        continue
                    with open ('/tmp/target' , 'w') as t:
                        t.write(line)
                    cmd = '/opt/ltp/runltp -f /tmp/target -C %s -q -l %s -o %s -T /dev/null' % (log_failed, log_output, log_output)
                    utils.run(cmd, ignore_status=True, verbose=False)
                    # /dev/loop# creation will be taken care by the runltp

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
