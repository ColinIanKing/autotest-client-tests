import os
from autotest.client import test, utils


class ubuntu_boot(test.test):
    version = 1

    def run_once(self, test_time=10, exit_on_error=True, set_time=True):
        cmd = "uname -a"
        utils.system(cmd)
        cmd = "lsb_release"
        utils.system(cmd)
