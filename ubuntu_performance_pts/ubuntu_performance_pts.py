#
#
import os
import platform
import time
import re
from autotest.client import test, utils

force_times_to_run = 8

class ubuntu_performance_pts(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'zip',
            'unzip',
            'zlib1g-dev',
            'php-cli',
            'php-xml',
            'libssl1.0-dev',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()

        self.results = utils.system_output('dpkg -i %s' % os.path.join(self.bindir, 'phoronix-test-suite_7.8.0_all.deb'), retain_output=True)
        self.results += utils.system_output('phoronix-test-suite enterprise-setup', retain_output=True)
        self.results += utils.system_output('yes n | phoronix-test-suite batch-setup', retain_output=True)

        print self.results

    def get_sysinfo(self):
        print 'date_ctime "' + time.ctime() + '"'
        print 'date_ns %-30.0f' % (time.time() * 1000000000)
        print 'kernel_version ' + platform.uname()[2]
        print 'cpus_online ' + utils.system_output('getconf _NPROCESSORS_ONLN', retain_output=True)
        print 'cpus_total ' + utils.system_output('getconf _NPROCESSORS_CONF', retain_output=True)
        print 'page_size ' + utils.system_output('getconf PAGE_SIZE', retain_output=True)
        print 'pages_availble ' + utils.system_output('getconf _AVPHYS_PAGES', retain_output=True)
        print 'pages_total ' + utils.system_output('getconf _PHYS_PAGES', retain_output=True)

    def print_stats(self, benchmark, results, fields):
        values = {}

        for line in results.splitlines():
            chunks = line.split()
            if len(chunks) > 1:
                for field in fields:
                    if chunks[0] == field + ':':
                        numbers = re.findall(r'-?\d+\.?\d*', chunks[1])
                        n = len(numbers)
                        #
                        #  Data may be prefixed ANSI escape sequences to
                        #  add pretty colors. Skip over all these and
                        #  grab the last number in the field
                        #
                        if n > 0:
                            values[field] = numbers[n - 1]
                        else:
                            values[field] = 0

        print
        for field in fields:
            print benchmark + "_" + field.lower(), values[field]

    def run_john_the_ripper_blowfish(self):
        results = utils.system_output('export PRESET_OPTIONS="john-the-ripper.run-test=Blowfish"; export FORCE_TIMES_TO_RUN=%d; phoronix-test-suite batch-benchmark john-the-ripper' % force_times_to_run)
        self.print_stats('john_the_ripper_blowfish', results, [ 'Average', 'Deviation' ])

    def run_john_the_ripper_des(self):
        results = utils.system_output('export PRESET_OPTIONS="john-the-ripper.run-test=Traditional DES"; export FORCE_TIMES_TO_RUN=%d; phoronix-test-suite batch-benchmark john-the-ripper' % force_times_to_run)
        self.print_stats('john_the_ripper_des', results, [ 'Average', 'Deviation' ])

    def run_openssl(self):
        results = utils.system_output('export FORCE_TIMES_TO_RUN=%d; phoronix-test-suite batch-benchmark openssl' % force_times_to_run)
        self.print_stats('openssl', results, [ 'Average', 'Deviation' ])

    def run_povray(self):
        results = utils.system_output('export FORCE_TIMES_TO_RUN=%d; phoronix-test-suite batch-benchmark povray' % force_times_to_run)
        self.print_stats('povray', results, [ 'Average', 'Deviation' ])

    def run_ttsiod_renderer(self):
        results = utils.system_output('export FORCE_TIMES_TO_RUN=%d; phoronix-test-suite batch-benchmark ttsiod-renderer' % force_times_to_run)
        self.print_stats('ttsiod_renderer', results, [ 'Average', 'Deviation' ])


    def run_once(self, test_name):
        run_funcs = {
            'setup': self.get_sysinfo,
            'john-the-ripper-blowfish' : self.run_john_the_ripper_blowfish,
            'john-the-ripper-des': self.run_john_the_ripper_des,
            'openssl': self.run_openssl,
            'povray': self.run_povray,
            'ttsiod-renderer': self.run_ttsiod_renderer,
        }

        if test_name in run_funcs:
                run_funcs[test_name]()
                print
        else:
                print 'cannot find test "%s"' % test_name


# vi:set ts=4 sw=4 expandtab syntax=python:
