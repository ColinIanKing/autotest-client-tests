#
#
import multiprocessing
import os
import platform
import re
import shutil
from autotest.client                        import test, utils

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
            'xfslibs-dev',
            'xfsprogs',
        ]
        gcc = 'gcc' if self.arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        if any(x in self.flavour for x in ['aws', 'azure', 'gcp', 'gke']):
            pkgs.append('linux-modules-extra-' + platform.uname()[2])

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.flavour = re.split('-\d*-', platform.uname()[2])[-1]
        self.arch = platform.processor()

    # setup
    #
    #    Automatically run when there is no autotest/client/tmp/<test-suite> directory
    #
    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        os.chdir(self.srcdir)
        shutil.rmtree('ltp', ignore_errors=True)
        branch = 'sru'
        cmd = 'git clone -b {} git://git.launchpad.net/~canonical-kernel-team/+git/ltp'.format(branch)
        utils.system_output(cmd, retain_output=True)

        # Print test suite HEAD SHA1 commit id for future reference
        os.chdir(os.path.join(self.srcdir, 'ltp'))
        title_local = utils.system_output("git log --oneline -1 | sed 's/(.*)//'", retain_output=False, verbose=False)
        title_upstream = utils.system_output("git log --oneline | grep -v SAUCE | head -1", retain_output=False, verbose=False)
        print("Latest commit in '{}' branch: {}".format(branch, title_local))
        print("Latest upstream commit: {}".format(title_upstream))

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


    # run_once
    #
    #    Driven by the control file for each individual test.
    #
    def run_once(self, test_name):
        if test_name == 'setup':
            return

        test_case = test_name.split(':')[1]

        if test_case == 'zram01':
            print("Setting LTP_TIMEOUT_MUL=5 for zram01 test (lp:1897556)")
            os.environ["LTP_TIMEOUT_MUL"] = '5'
        elif test_case in ['cve-2018-1000204 ', 'ioctl_sg01']:
            print("Setting LTP_TIMEOUT_MUL=3 for cve-2018-1000204 / ioctl_sg01 (lp:1899413, lp:1936886, lp:1949934)")
            os.environ["LTP_TIMEOUT_MUL"] = '3'
        elif test_case == 'fs_fill' and self.arch == 'ppc64le':
            print("Setting LTP_TIMEOUT_MUL=3 for fs_fill on PowerPC")
            os.environ["LTP_TIMEOUT_MUL"] = '3'

        cmd = '/opt/ltp/runltp -f /tmp/target -q -C /dev/null -l /dev/null -T /dev/null'
        print(utils.system_output(cmd, verbose=False))
        # /dev/loop# creation will be taken care by the runltp

    def cleanup(self, test_name):
        if test_name == 'setup':
            return

        # Restore the timeout multiplier
        if 'LTP_TIMEOUT_MUL' in os.environ:
            print("Restore timeout multiplier LTP_TIMEOUT_MUL back to default")
            del os.environ["LTP_TIMEOUT_MUL"]

# vi:set ts=4 sw=4 expandtab syntax=python:
