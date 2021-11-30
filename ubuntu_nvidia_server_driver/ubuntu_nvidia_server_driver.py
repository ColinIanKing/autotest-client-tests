import os
from autotest.client import test, utils

p_dir = os.path.dirname(os.path.abspath(__file__))
sh_executable = os.path.join(p_dir, "ubuntu_nvidia_server_driver.sh")


class ubuntu_nvidia_server_driver(test.test):
    version = 1

    def initialize(self):
        pass

    def setup(self):
        cmd = "{} setup".format(sh_executable)
        utils.system(cmd)

    def compare_kernel_modules(self):
        cmd = "{} test".format(sh_executable)
        utils.system(cmd)

    def run_once(self, test_name):
        if test_name == "load":
            self.compare_kernel_modules()

            print("")
            print("{} has run.".format(test_name))

        print("")

    def postprocess_iteration(self):
        pass
