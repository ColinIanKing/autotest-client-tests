#
#
import multiprocessing
import os
import platform
import re
import time
from autotest.client                        import test, utils
from autotest.client.shared     import error

class ubuntu_ltp(test.test):
    version = 1

    def install_required_pkgs(self):
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'automake',
            'bison',
            'build-essential',
            'byacc',
            'flex',
            'git',
            'keyutils',
            'libacl1-dev',
            'libaio-dev',
            'libcap-dev',
            'libmm-dev',
            'libnuma-dev',
            'libsctp-dev',
            'libselinux1-dev',
            'libssl-dev',
            'libtirpc-dev',
            'pkg-config',
            'quota',
            'virt-what',
            'xfslibs-dev',
            'xfsprogs',
        ]
        gcc = 'gcc' if self.arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        if self.flavour in ['aws', 'azure', 'azure-fips', 'gcp', 'gke', 'gkeop']:
             pkgs.append('linux-modules-extra-' + self.flavour + '*')

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.flavour = re.split('-\d*-', platform.uname()[2])[-1]
        self.arch = platform.processor()
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

        cmd = 'cat %s > /tmp/skip' % os.path.join(self.bindir, 'skip')
        utils.system_output(cmd)

    # run_once
    #
    #    Driven by the control file for each individual test.
    #
    def run_once(self, test_name):
        if test_name == 'setup':
            return
        fn = '/tmp/syscalls-' + time.strftime("%h%d-%H%M%S")
        log_failed = fn + '.failed'
        log_output = fn + '.output'

        fn = '/opt/ltp/runtest/%s' % (test_name)

        print("Setting LTP_TIMEOUT_MUL exceptions...")
        timeout_cases = { 'zram01': '5'}
        if utils.system_output('virt-what', verbose=False):
            print("Running in VM, set timeout multiplier LTP_TIMEOUT_MUL=3 for memcg_test_3 (lp:1836694)")
            timeout_cases['memcg_test_3'] = '3'
        if self.flavour in ['azure', 'oracle']:
            print("Running on Azure / Oracle, set timeout multiplier LTP_TIMEOUT_MUL=3 for cve-2018-1000204 / ioctl_sg01 (lp:1899413)")
            timeout_cases['ioctl_sg01'] = '3'
        if self.arch in ['ppc64le']:
            print("Running on PowerPC, set timeout multiplier LTP_TIMEOUT_MUL=3 for fs_fill (lp:1878763)")
            timeout_cases['fs_fill'] = '3'

        os.environ["LTP_TIMEOUT_MUL"] = '1'
        with open(fn , 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    with open ('/tmp/target' , 'w') as t:
                        t.write(line)

                    for _case in timeout_cases:
                        if _case in line:
                            os.environ["LTP_TIMEOUT_MUL"] = timeout_cases[_case]
                            break

                    cmd = '/opt/ltp/runltp -f /tmp/target -S /tmp/skip -C %s -q -l %s -o %s -T /dev/null' % (log_failed, log_output, log_output)
                    utils.run(cmd, ignore_status=True, verbose=False)
                    # /dev/loop# creation will be taken care by the runltp

                    # Restore the timeout multiplier
                    os.environ["LTP_TIMEOUT_MUL"] = '1'

        num_failed = sum(1 for line in open(log_failed))
        print("== Test Suite Summary ==")
        print("{} test cases failed".format(num_failed))

        if num_failed > 0:
            cmd = "awk '{print$1}' " + log_failed + " | sort | uniq | tr '\n' ' '"
            failed_list = utils.system_output(cmd, retain_output=False, verbose=False)
            print("Failed test cases : %s" % failed_list)

        cmd = 'cat ' + log_output
        utils.system_output(cmd, retain_output=True, verbose=False)

        if num_failed > 0:
            raise error.TestError('Test failed for ' + test_name)

# vi:set ts=4 sw=4 expandtab syntax=python:
