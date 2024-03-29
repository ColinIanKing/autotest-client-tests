#
#
import os
import shutil
from autotest.client                        import test, utils

class ubuntu_unionmount_ovlfs(test.test):
    version = 1

    def install_required_pkgs(self):
        pkgs = [
            'git', 'python3',
        ]

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        if not os.path.exists('/lower'):
            os.mkdir('/lower')
        if not os.path.exists('/upper'):
            os.mkdir('/upper')

    # setup
    #
    #    Automatically run when there is no autotest/client/tmp/<test-suite> directory
    #
    def setup(self):
        self.install_required_pkgs()
        os.chdir(self.srcdir)
        shutil.rmtree('unionmount-testsuite', ignore_errors=True)
        cmd = 'git clone --depth=1 https://github.com/amir73il/unionmount-testsuite.git'
        self.results = utils.system_output(cmd, retain_output=True)
        # Print test suite HEAD SHA1 commit id for future reference
        os.chdir(os.path.join(self.srcdir, 'unionmount-testsuite'))
        sha1 = utils.system_output('git rev-parse --short HEAD', retain_output=False, verbose=False)
        print("Test suite HEAD SHA1: {}".format(sha1))

        # We are using a new github fork of unionmount_overlayfs_suite, this patch is
        # no longer needed. -sfeole 8/21/2019
        # cmd = 'patch -p1 < %s/0001-Fix-check-for-file-on-overlayfs.patch' % self.bindir
        # utils.system(cmd)

    # run_once
    #
    #    Driven by the control file for each individual test.
    #
    def run_once(self, test_name):
        os.chdir(os.path.join(self.srcdir, 'unionmount-testsuite'))

        if test_name == 'unionmount':
            cmd = './run --um'
            self.results = utils.system_output(cmd, retain_output=True)
        elif test_name == 'overlayfs':
            cmd = './run --ov'
            self.results = utils.system_output(cmd, retain_output=True)

    def cleanup(self, test_name):
        if test_name == 'setup':
            return
        print("Clean up after the test...")
        if os.path.ismount('/lower'):
            utils.run('umount /lower')
        if os.path.ismount('/upper'):
            utils.run('umount /upper')
        if os.path.ismount('/mnt'):
            utils.run('umount /mnt')
        # We didn't create /mnt, so do not remove it here
        os.rmdir('/lower')
        os.rmdir('/upper')

# vi:set ts=4 sw=4 expandtab syntax=python:
