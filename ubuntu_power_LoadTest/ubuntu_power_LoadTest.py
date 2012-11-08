import os, shutil
from autotest.client import test, utils


class ubuntu_power_LoadTest(test.test):
    version = 1

    def setup(self):
        pass

    def initialize(self):
        pass

    def run_once(self):
        ext_path = os.path.join(os.path.dirname(__file__), 'extension')

        utils.run('DISPLAY=:0 chromium-browser --load-extension=%s --user-data-dir=/home/bradf' % ext_path, timeout = 1 * 60)

# vi:set ts=4 sw=4 expandtab syntax=python:
