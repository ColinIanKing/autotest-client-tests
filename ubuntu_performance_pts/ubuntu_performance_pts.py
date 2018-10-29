#
#
import os
import platform
import time
import re
import getpass
import pwd
from autotest.client import test, utils

#
#  Number of times to run specific test
#
test_iterations = 3

#
#  Number of times to run in Phoronix Test Suite to
#  get some sane stats. Normally this is 3, but we
#  can override this. For now, keep the default.
#
#force_times_to_run = "export FORCE_TIMES_TO_RUN=5; "
force_times_to_run = ""

class ubuntu_performance_pts(test.test):
    version = 2

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
            'gdb',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup_config(self, home_dir):
        pts_dir = os.path.join(home_dir, '.phoronix-test-suite')
        self.results = utils.system_output('mkdir -p %s' % pts_dir)
        self.results += utils.system_output('cp %s %s' % (os.path.join(self.bindir, 'user-config.xml'), pts_dir))
        return self.results

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()

        username = getpass.getuser()
        self.results = utils.system_output('cp %s %s' % (os.path.join(self.bindir, 'user-config.xml'), os.path.join('/etc','phoronix-test-suite.xml')))
        self.results += self.setup_config(pwd.getpwnam(username)[5])
        self.results += self.setup_config(os.path.expanduser("~"))

        self.results += utils.system_output('dpkg -i %s' % os.path.join(self.bindir, 'phoronix-test-suite_7.8.0_all.deb'), retain_output=True)
        self.results += utils.system_output('phoronix-test-suite enterprise-setup', retain_output=True)
        self.results += utils.system_output('yes n | phoronix-test-suite batch-setup', retain_output=True)

        print self.results

    def get_sysinfo(self):
        print 'date_ctime "' + time.ctime() + '"'
        print 'date_ns %-30.0f' % (time.time() * 1000000000)
        print 'kernel_version ' + platform.uname()[2]
        print 'hostname ' + platform.node()
        print 'virtualization ' + utils.system_output('systemd-detect-virt || true', retain_output=True)
        print 'cpus_online ' + utils.system_output('getconf _NPROCESSORS_ONLN', retain_output=True)
        print 'cpus_total ' + utils.system_output('getconf _NPROCESSORS_CONF', retain_output=True)
        print 'page_size ' + utils.system_output('getconf PAGE_SIZE', retain_output=True)
        print 'pages_availble ' + utils.system_output('getconf _AVPHYS_PAGES', retain_output=True)
        print 'pages_total ' + utils.system_output('getconf _PHYS_PAGES', retain_output=True)

    def get_stats(self, results, fields):
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

        return values

    def print_stats(self, benchmark, command):
        fields = [ 'Average', 'Deviation' ]
        values = {}
        test_pass = True

        for i in range(test_iterations):
            results = utils.system_output(command)
            values[i] = self.get_stats(results, fields)

            print
            print "Test %d of %d:" % (i + 1, test_iterations)
            for field in fields:
                print benchmark + "_" + field.lower() + "[%d] %s" % (i, values[i][field])

        #
        #  Compute min/max/average:
        #
        field = 'Average'
        v = [ float(values[i][field]) for i in values ]
        maximum = max(v)
        minimum = min(v)
        average = sum(v) / float(len(v))
        max_err = (maximum - minimum) / average * 100.0

        print
        print benchmark + "_" + field.lower() + "_minimum", minimum
        print benchmark + "_" + field.lower() + "_maximum", maximum
        print benchmark + "_" + field.lower() + "_average", average
        print benchmark + "_" + field.lower() + "_maximum_error %.2f%%" % (max_err)
        print

        if max_err > 5.0:
            print "FAIL: maximum error is greater than 5%"
            test_pass = False

        if test_pass:
            print "PASS: test passes specified performance thresholds"

    def run_john_the_ripper_blowfish(self):
        cmd = 'export PRESET_OPTIONS="john-the-ripper.run-test=Blowfish"; %s phoronix-test-suite batch-benchmark john-the-ripper' % force_times_to_run
        self.print_stats('john_the_ripper_blowfish', cmd)

    def run_john_the_ripper_des(self):
        cmd = 'export PRESET_OPTIONS="john-the-ripper.run-test=Traditional DES"; %s phoronix-test-suite batch-benchmark john-the-ripper' % force_times_to_run
        self.print_stats('john_the_ripper_des', cmd)

    def run_openssl(self):
        cmd = '%s phoronix-test-suite batch-benchmark openssl' % force_times_to_run
        self.print_stats('openssl', cmd)

    def run_povray(self):
        cmd = '%s phoronix-test-suite batch-benchmark povray' % force_times_to_run
        self.print_stats('povray', cmd)

    def run_ttsiod_renderer(self):
        cmd = '%s phoronix-test-suite batch-benchmark ttsiod-renderer' % force_times_to_run
        self.print_stats('ttsiod_renderer', cmd)


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
