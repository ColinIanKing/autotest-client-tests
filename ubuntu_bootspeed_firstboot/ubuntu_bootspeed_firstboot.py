import os
import platform
from autotest.client import test, utils


class ubuntu_bootspeed_firstboot(test.test):
    version = 1

    def install_required_pkgs(self):
        pass
        # arch   = platform.processor()
        # series = platform.dist()[2]

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()

    def run_once(self, test_time=10, exit_on_error=True, set_time=True):

        # We have been deployed onto a single instance on a cloud. We want to
        # create N other instances just like this one and measure the firstboot
        # bootspeed.
        #

        os.environ['BS_CLOUD']          = os.environ['CLOUD']
        os.environ['BS_SERIES']         = platform.dist()[2]
        os.environ['BS_INSTNANCE_TYPE'] = os.environ['INSTANCE_TYPE']
        os.environ['BS_CLOUD_REGION']   = os.environ['REGION']
        os.environ['BS_ARCH']           = 'x86'
        os.environ['BS_KERNEL_PACKAGE'] = 'linux-aws'
        os.environ['BS_KERNEL_FLAVOUR'] = 'aws'
        os.environ['BS_INSTANCE_NAME']  = 'foo'

        cmd = 'bs-test'
        utils.system(cmd)
