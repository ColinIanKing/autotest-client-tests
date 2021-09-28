#
#
import multiprocessing
import os
import platform
import re
import sys
import shutil
import signal
from autotest.client import test, utils
from autotest.client.shared import error

# python is redefining the SIGXFSZ handler internally, blocking the delivery of
# this signal to any forked task. Make sure to restore the default signal
# handler for SIGXFSZ before running any test.
try:
    signal.signal(signal.SIGXFSZ, signal.SIG_DFL)
except Exception, e:
    print(e)
    sys.stdout.flush()


class ubuntu_ltp_controllers(test.test):
    version = 1

    def install_required_pkgs(self):
        arch = platform.processor()

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
            'pkg-config',
            'quota',
            'virt-what',
            'xfslibs-dev',
            'xfsprogs',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        if self.flavour in ['aws', 'azure', 'azure-fips', 'gcp', 'gcp-fips', 'gke', 'gkeop']:
            if not (self.flavour == 'aws' and self.series == 'trusty'):
                pkgs.append('linux-modules-extra-' + self.flavour + '*')
        if self.flavour not in ['kvm']:
            pkgs.append('nfs-kernel-server')
        if self.series not in ['trusty']:
            pkgs.append('haveged')
        if self.series in ['xenial', 'bionic', 'focal']:
            pkgs.append('python-packaging')

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        try:
            self.series = platform.dist()[2]
        except AttributeError:
            import distro
            self.series = distro.codename()
        self.flavour = re.split('-\d*-', platform.uname()[2])[-1]
        self.kernel = platform.uname()[2].split('-')[0]

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
        if self.series in ['trusty', 'xenial']:
            branch = 'sru-' + self.series
            print("Use a fixed branch for ESM series - {}".format(branch))

        cmd = 'git clone -b {} --depth 1 git://kernel.ubuntu.com/ubuntu/ltp.git'.format(branch)
        utils.system_output(cmd, retain_output=True)

        # Print test suite HEAD SHA1 commit id for future reference
        os.chdir(os.path.join(self.srcdir, 'ltp'))
        title = utils.system_output("git log --oneline -1 | sed 's/(.*)//'", retain_output=False, verbose=False)
        print("Latest commit in '{}' branch: {}".format(branch, title))

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

        cmd = '/opt/ltp/runltp -f /tmp/target -q -C /dev/null -l /dev/null -T /dev/null'
        print(utils.system_output(cmd, verbose=False))
        # /dev/loop# creation will be taken care by the runltp

# vi:set ts=4 sw=4 expandtab syntax=python:
