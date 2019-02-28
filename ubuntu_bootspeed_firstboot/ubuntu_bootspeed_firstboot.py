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

        params = {
            'cloud'         : os.environ['CLOUD'],
            'iname'         : os.environ['REGION'],
            'series'        : platform.dist()[2],
            'instance_type' : os.environ['INSTANCE_TYPE'],
            'region'        : os.environ['REGION'],
            'arch'          : 'x86',
        }
        ckct_root = os.path.expanduser('~') + '/ckct'
        deploy = 'sut-deploy {cloud} {iname} {series} {instance_type} --region {region} --arch {arch}'.format(**params)
        cmd = ckct_root + '/' + deploy

        utils.system('echo' + ' ' + cmd)
