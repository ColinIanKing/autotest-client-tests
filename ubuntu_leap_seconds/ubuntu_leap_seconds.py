import os, shutil
from autotest.client import test, utils


class ubuntu_leap_seconds(test.test):
    version = 1

    def setup(self):
        shutil.copyfile(os.path.join(self.bindir, 'leap_seconds.c'),
                        os.path.join(self.srcdir, 'leap_seconds.c'))
        os.chdir(self.bindir)
        os.chdir(self.srcdir)
        utils.system(utils.get_cc() + ' leap_seconds.c -D_BSD_SOURCE -D_POSIX_C_SOURCE=200112 -o leap_seconds -lrt')

    def initialize(self):
        self.job.require_gcc()

    def run_once(self, test_time=10, exit_on_error=True, set_time=True):
        cmd = os.path.join(self.srcdir, 'leap_seconds')

        args = ''
        if set_time:
            args += ' -s'

        if exit_on_error:
            args += ' -x'

        args += ' -t %d' % test_time
        utils.system(cmd + ' ' + args)

