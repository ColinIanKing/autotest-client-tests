#
#
import os
import platform
from autotest.client                        import test, utils

class ubuntu_kernel_selftests(test.test):
    version = 1

    def setup(self):
        os.chdir(self.srcdir)
        self.job.require_gcc()
        series = platform.dist()[2]

        # Use a local repo for manual testing. If it does not exist, then clone from the master
        # repository.
        #
        repo = os.environ['HOME'] + '/ubuntu/ubuntu-%s' % series
        if os.path.exists(repo) == True:
            cmd = 'git clone -q %s linux' % repo
            utils.system(cmd)

        # No local repository, so clone from the master repo.
        #
        if os.path.exists('linux') == False:
            cmd = 'git clone https://git.launchpad.net/~ubuntu-kernel/ubuntu/+source/linux/+git/%s linux' % series
            utils.system(cmd)

    def run_once(self, test_name):
        os.chdir(self.srcdir)
        cmd = "sudo make -C linux/tools/testing/selftests/%s all run_tests" % test_name
        utils.system(cmd)

# vi:set ts=4 sw=4 expandtab syntax=python:
