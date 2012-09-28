import os
from autotest.client import test, utils
import sys

class power_consumption(test.test):
    version = 1

    def initialize(self):
        self.job.require_gcc()

    def setup(self, instrument_lib_tarball = 'instrument-lib.tar.bz2'):
        instrument_lib_tarball = utils.unmap_url(self.bindir, instrument_lib_tarball, self.tmpdir)
        utils.extract_tarball_to_dir(instrument_lib_tarball, self.srcdir)

	#
	# make the tools
	#
	statstool = os.path.join(self.srcdir, 'statstool')
	os.chdir(statstool)
	utils.make()
	
    def run_once(self, test_name):
        if test_name == 'setup':
            return

        os.chdir(self.srcdir)
	#
	#  Meter and tools configuration
	#
	# Env variables METER_ADDR, METER_PORT, and METER_TAGPORT must be passed in to the test
        # See the control file
	os.putenv('LOGMETER', os.path.join(self.srcdir, 'logmeter'))
	os.putenv('SENDTAG', os.path.join(self.srcdir, 'sendtag'))
	os.putenv('STATSTOOL', os.path.join(os.path.join(self.srcdir, 'statstool'), 'statstool'))
	os.putenv('SAMPLES_LOG', os.path.join(os.path.join(self.tmpdir, 'samples.log')))
	os.putenv('STATISTICS_LOG', os.path.join(os.path.join(self.tmpdir, 'statistics.log')))
	os.putenv('SAMPLES', '60')
	os.putenv('SAMPLE_INTERVAL', '5')
	os.putenv('SETTLE_DURATION', '30')
	os.putenv('SCRIPT_PATH', os.path.join(self.bindir, 'power_consumption_tests'))

	script = os.path.join(os.path.join(self.bindir, 'power_consumption_tests'), test_name)
        output = utils.system_output(script, retain_output=True)

        keylist = {}
        for line in output.splitlines():
            split = line.split(':')
            keylist[split[1]] = split[2]

        self.write_perf_keyval(keylist)

# vi:set ts=4 sw=4 expandtab:
