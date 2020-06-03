import os
import platform
from autotest.client import test, utils
import sys

class power_consumption(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'stress',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self, instrument_lib_tarball='instrument-lib.tar.bz2'):
        self.install_required_pkgs()
        self.job.require_gcc()
        instrument_lib_tarball = utils.unmap_url(self.bindir, instrument_lib_tarball, self.tmpdir)
        instrument_lib_srcpath = os.path.join(self.srcdir, 'instrument-lib')
        utils.extract_tarball_to_dir(instrument_lib_tarball, instrument_lib_srcpath)

        sys.stderr.write('SRCPATH' + instrument_lib_srcpath + '\n')

        stress_ng_srcpath = os.path.join(self.srcdir, 'stress-ng')
        stress_ng_tarball = 'stress-ng.tar.bz2'
        stress_ng_tarball = utils.unmap_url(self.bindir, stress_ng_tarball, stress_ng_srcpath)
        utils.extract_tarball_to_dir(stress_ng_tarball, stress_ng_srcpath)

        #
        # make instrument lib statstool
        #
        statstool = os.path.join(instrument_lib_srcpath, 'statstool')
        os.chdir(statstool)
        utils.make()

        #
        # make stress-ng
        #
        os.chdir(stress_ng_srcpath)
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
        instrument_lib_srcpath = os.path.join(self.srcdir, 'instrument-lib')
        stress_ng_srcpath = os.path.join(self.srcdir, 'stress-ng')

        os.putenv('LOGMETER', os.path.join(instrument_lib_srcpath, 'logmeter'))
        os.putenv('SENDTAG', os.path.join(instrument_lib_srcpath, 'sendtag'))
        os.putenv('STATSTOOL', os.path.join(os.path.join(instrument_lib_srcpath, 'statstool'), 'statstool'))
        os.putenv('SAMPLES_LOG', os.path.join(os.path.join(self.tmpdir, 'samples.log')))
        os.putenv('STATISTICS_LOG', os.path.join(os.path.join(self.tmpdir, 'statistics.log')))
        os.putenv('SAMPLES', '150')
        os.putenv('SAMPLE_INTERVAL', '2')
        os.putenv('SETTLE_DURATION', '30')
        os.putenv('SCRIPT_PATH', os.path.join(self.bindir, 'power_consumption_tests'))
        os.putenv('STRESS', os.path.join(stress_ng_srcpath, 'stress-ng'))

        script = os.path.join(os.path.join(self.bindir, 'power_consumption_tests'), test_name)
        output = utils.system_output(script, retain_output=True)

        keylist = {}
        for line in output.splitlines():
            split = line.split(':')
            keylist[split[1]] = split[2]

        self.write_perf_keyval(keylist)

# vi:set ts=4 sw=4 expandtab:
