#
#
import os
import platform
import time
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
            'xfslibs-dev',
            'xfsprogs',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        try:
            cloud  = os.environ['CLOUD']
            if cloud in ['azure', 'gcp', 'gke']:
                 pkgs.append('linux-modules-extra-' + cloud + '*')
        except KeyError:
            pass

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
        with open(fn , 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    with open ('/tmp/target' , 'w') as t:
                        t.write(line)
                    cmd = '/opt/ltp/runltp -f /tmp/target -C %s -q -l %s -o %s -T /dev/null' % (log_failed, log_output, log_output)
                    utils.run(cmd, ignore_status=True, verbose=False)
                    # /dev/loop# creation will be taken care by the runltp

        num_failed = sum(1 for line in open(log_failed))
        print("== Test Suite Summary ==")
        print("{} test cases failed").format(num_failed)

        if num_failed > 0:
            cmd = "awk '{print$1}' " + log_failed + " | sort | uniq | tr '\n' ' '"
            failed_list = utils.system_output(cmd, retain_output=False, verbose=False)
            print("Failed test cases : %s" % failed_list)
            cmd = 'cat ' + log_output
            utils.system_output(cmd, retain_output=True, verbose=False)
            raise error.TestFail()

# vi:set ts=4 sw=4 expandtab syntax=python:
