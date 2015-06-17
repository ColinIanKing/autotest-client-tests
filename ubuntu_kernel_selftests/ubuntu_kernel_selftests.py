#
#
import os
from autotest.client                        import test, utils

#
# Dictionary of kernel versions and releases for which self tests are supported.
#
releases = { '3.13':'trusty', '3.16':'utopic', '3.19':'vivid', '4.0':'wily' };

class ubuntu_kernel_selftests(test.test):
    version = 1

    # Extract the running kernel version and pair it with an Ubuntu release. Knowing
    # that allows us to pull the right repository.
    #
    release = os.uname()
    uname = release[2]
    version = uname[0:4]

    def setup(self):
        os.chdir(self.srcdir)
        self.job.require_gcc()

        # Use a local repo for manual testing. If it does not exist, then clone from the master
        # repository.
        #
        repo = os.environ['HOME'] + '/ubuntu/ubuntu-%s' % releases[self.version]
        if os.path.exists(repo) == True:
            cmd = 'git clone -q %s linux' % repo
            utils.system(cmd)

        # No local repository, so clone from the master repo.
        #
        if os.path.exists('linux') == False:
            cmd = 'git clone http://kernel.ubuntu.com/git-repos/ubuntu/ubuntu-%s.git linux' % releases[self.version]
            utils.system(cmd)

    def run_once(self, test_name):
        os.chdir(self.srcdir)
        cmd = "sudo make -C linux/tools/testing/selftests/%s all run_tests" % test_name
        utils.system(cmd)

# vi:set ts=4 sw=4 expandtab syntax=python:
