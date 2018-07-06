import os
from autotest.client import test, utils

import sys

class wakeup_events(test.test):
    version = 1

    def initialize(self):
        pass

    def setup(self, instrument_lib_tarball = 'eventstat.tar.bz2'):
        self.job.require_gcc()
        instrument_lib_tarball = utils.unmap_url(self.bindir, instrument_lib_tarball, self.tmpdir)
        utils.extract_tarball_to_dir(instrument_lib_tarball, self.srcdir)

	#
	# make the tools
	#
	tool = os.path.join(self.srcdir, 'eventstat')
	os.chdir(self.srcdir)
	utils.make()
	
    def run_once(self, test_name):
        if test_name == 'setup':
            return

        os.chdir(self.srcdir)
	#
	#  Meter and tools configuration
	#
	os.putenv('DURATION', '600')
	os.putenv('EVENTSTAT', os.path.join(self.srcdir, 'eventstat'))

	script = os.path.join(os.path.join(self.bindir, 'wakeup_events_tests'), test_name)
        output = utils.system_output(script, retain_output=True)

        keylist = {}
        for line in output.splitlines():
            split = line.split('\t')
            keylist[split[0]] = split[1]

	print sys.stderr, keylist
        self.write_perf_keyval(keylist)

# vi:set ts=4 sw=4 expandtab:
