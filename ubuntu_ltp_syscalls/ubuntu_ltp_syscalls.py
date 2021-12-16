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


class ubuntu_ltp_syscalls(test.test):
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

        if any(x in self.flavour for x in ['aws', 'azure', 'gcp', 'gke']):
            if not (self.flavour == 'aws' and self.series == 'trusty'):
                pkgs.append('linux-modules-extra-' + platform.uname()[2])
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

        cmd = 'git clone -b {} --depth 1 git://git.launchpad.net/~canonical-kernel-team/+git/ltp'.format(branch)
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

    def should_stop_timesyncd(self, test, action):
        # Check if systemd-timesyncd is running before the test, if not, do not try to stop / start it
        status_output = utils.system_output('systemctl status systemd-timesyncd 2>&1', ignore_status=True, verbose=False)
        if action == 'stop':
            targets = ['Active: inactive', 'systemd-timesyncd.service could not be found', 'Loaded: masked']
        else:
            targets = ['Active: active', 'systemd-timesyncd.service could not be found', 'Loaded: masked']
        skip_timesyncd = any(string in status_output for string in targets)
        # trusty does not have systemd-timesyncd
        return test in ['leapsec01', 'stime01', 'settimeofday01', 'clock_settime01'] and self.series != 'trusty' and not skip_timesyncd

    # run_once
    #
    #    Driven by the control file for each individual test.
    #
    def run_once(self, test_name):
        if test_name == 'setup':
            return

        LTP_TIMEOUT_MUL = '3'

        # Set the timeout multiplier exclusively for getrandom02 (lp:1831235) in a VM
        if test_name == 'getrandom02':
            if utils.system_output('virt-what', verbose=False):
                print("Running in VM, set timeout multiplier LTP_TIMEOUT_MUL={} (lp:1797327) for getrandom02".format(LTP_TIMEOUT_MUL))
                os.environ["LTP_TIMEOUT_MUL"] = LTP_TIMEOUT_MUL
        # Set the timeout multiplier for ioctl_sg01 (lp:1895281, lp:1936886)
        elif test_name == 'ioctl_sg01':
            print("Set timeout multiplier LTP_TIMEOUT_MUL>1 (lp:1895281, lp:1936886) for ioctl_sg01")
            os.environ["LTP_TIMEOUT_MUL"] = LTP_TIMEOUT_MUL
        elif test_name == 'fanotify07' and self.kernel == '4.4.0':
            raise error.TestError("fanotify07 (lp:1775165) won't fix on T/X and blocking test to finish properly (lp:1944545), mark it as failed directly")

        # Stop timesyncd when testing time change
        if self.should_stop_timesyncd(test_name, 'stop'):
            utils.run('systemctl stop systemd-timesyncd')

        cmd = '/opt/ltp/runltp -f /tmp/target -q -C /dev/null -l /dev/null -T /dev/null'
        print(utils.system_output(cmd, verbose=False))
        # /dev/loop# creation will be taken care by the runltp

    def cleanup(self, test_name):
        if test_name == 'setup':
            return

        # Restart timesyncd after the test
        if self.should_stop_timesyncd(test_name, 'start'):
            utils.run('systemctl start systemd-timesyncd')

        # Restore the timeout multiplier
        if 'LTP_TIMEOUT_MUL' in os.environ:
            print("Restore timeout multiplier LTP_TIMEOUT_MUL back to default")
            del os.environ["LTP_TIMEOUT_MUL"]
# vi:set ts=4 sw=4 expandtab syntax=python:
