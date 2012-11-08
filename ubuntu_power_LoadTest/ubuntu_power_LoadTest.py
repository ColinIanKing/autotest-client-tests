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
        ck = os.path.join(os.path.dirname(__file__), 'chromium-browser-killer')
        utils.run_parallel(['DISPLAY=:0 chromium-browser --user-data-dir=/home/bradf --load-extension=%s' % ext_path, ck])


# vi:set ts=4 sw=4 expandtab syntax=python:
