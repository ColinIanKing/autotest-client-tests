#
#
from autotest.client                        import test
from autotest.client.shared                 import error

class ubuntu_simple_py_example(test.test):
    version = 1

    def initialize(self):
        pass

    def run_once(self, ssid=None, wpapsk='', test_time=10, exit_on_error=True, set_time=True):
        print('looks fine')

        # Raise error.TestError if you want the test to fail.
        #
        #raise error.TestError('Yup, this failed!')

# vi:set ts=4 sw=4 expandtab syntax=python:
