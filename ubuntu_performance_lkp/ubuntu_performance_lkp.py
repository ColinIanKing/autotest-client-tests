#
#
import os
from autotest.client import test, utils
from math import sqrt
import platform

#
# Number of test iterations to get min/max/average stats
#
test_iterations = 3

class ubuntu_performance_lkp(test.test):
    version = 1

    def is_number(self, s):
        try:
            f = float(s)
            return True
        except:
            return False

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self, lkp_jobs):
        self.install_required_pkgs()
        self.job.require_gcc()

        utils.system_output('apt-get install git', retain_output=True)

        os.chdir(self.srcdir)
        self.results = utils.system_output('git clone https://github.com/intel/lkp-tests', retain_output=True)
        os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
        self.results = utils.system_output('git checkout -b stable d719cf911a0bd0b2b6528c7220ccb41cf69c726f', retain_output=True)

        utils.system_output('make install', retain_output=True)
        utils.system_output('lkp install', retain_output=True)

        for lkp_job in lkp_jobs:
            print "setting up " + lkp_job
            utils.system_output('lkp install jobs/%s || true' % lkp_job, retain_output=True)
            utils.system_output('lkp split jobs/%s || true' % lkp_job, retain_output=True)

    def run_aim9(self, lkp_job, lkp_jobs, test_name):
        values = []
        for i in range(test_iterations):
            print "Testing %s: %d of %d" % (lkp_job, i + 1, test_iterations)
            os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
            cmd = 'sudo lkp run %s' % lkp_job
            self.results = utils.system_output(cmd, retain_output=True)

            #
            # parse text, find ops/sec in fields as follows:
            #
            # ------------------------------------------------------------------------------------------------------------
            #   Test        Test        Elapsed  Iteration    Iteration          Operation
            #  Number       Name      Time (sec)   Count   Rate (loops/sec)    Rate (ops/sec)
            #  ------------------------------------------------------------------------------------------------------------
            #       1 brk_test           300.00      42763  142.54333      2423236.67 System Memory Allocations/second
            # ------------------------------------------------------------------------------------------------------------
            found_dashes = False;
            for line in self.results.splitlines():
                chunks = line.split()
                if len(chunks) > 0 and '---------' in chunks[0]:
                    found_dashes = True;
                elif found_dashes and len(chunks) > 5 and chunks[0] == '1' and self.is_number(chunks[5]):
                    values.append(float(chunks[5]))
                    found_dashes = False

        print "%s_bogoops" % (test_name), "%.3f " * len(values) % tuple(values)
        return values

    def run_hackbench(self, lkp_job, lkp_jobs, test_name):
        values = []
        print "Testing %s: 1 of 1" % lkp_job
        os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
        cmd = 'sudo lkp run %s' % lkp_job
        self.results = utils.system_output(cmd, retain_output=True)
        #
        # parse text, find Time: fields in multiple repeats of results such as:
        #
        # 2018-12-18 10:57:33 /usr/bin/hackbench -g 32 --process threads -l 3750
        # Running in process mode with 32 groups using 40 file descriptors each (== 1280 tasks)
        # Each sender will pass 3750 messages of 100 bytes
        # Time: 29.915
        #
        for line in self.results.splitlines():
            chunks = line.split()
            if len(chunks) == 2 and chunks[0] == "Time:":
                values.append(float(chunks[1]))

        print "%s_seconds" % (test_name), "%.3f " * len(values) % tuple(values)
        return values

    def run_vm_scalability(self, lkp_job, lkp_jobs, test_name):
        values = []
        for i in range(test_iterations):
            print "Testing %s: %d of %d" % (lkp_job, i + 1, test_iterations)
            os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
            cmd = 'sudo lkp run %s' % lkp_job
            self.results = utils.system_output(cmd, retain_output=True)

            #
            # parse text, find KB/s data in fields as follows:
            #
            # 53614772232 bytes / 300627955 usecs = 174162 KB/s
            # 53358395400 bytes / 300632043 usecs = 173327 KB/s
            # 56508841992 bytes / 300632313 usecs = 183561 KB/s
            # 56203182088 bytes / 300632709 usecs = 182568 KB/s
            #
            for line in self.results.splitlines():
                chunks = line.split()
                if len(chunks) >= 8 and chunks[1] == "bytes" and chunks[4] == "usecs" and chunks[7] == "KB/s":
                    values.append(float(chunks[6]))

        print "%s_kb_per_sec" % (test_name), "%.3f " * len(values) % tuple(values)
        return values

    def run_once(self, lkp_job, sub_job, lkp_jobs):
        if lkp_job == 'setup':
            #self.setup(lkp_jobs)
            return

        job_funcs = {
            'aim9.yaml':           self.run_aim9,
            'hackbench.yaml':      self.run_hackbench,
            'vm-scalability.yaml': self.run_vm_scalability,
        }

        test_name = sub_job
        test_name = test_name.replace("-", "_")
        test_pass = True

        print
        if lkp_job in job_funcs:
            values = job_funcs[lkp_job](sub_job, lkp_jobs, test_name)
        else:
            print "Cannot find running/parser for %s" % lkp_job
            return

        minimum = min(values)
        maximum = max(values)
        average = sum(values) / len(values)
        max_err = (maximum - minimum) / average * 100.0

        if len(values) > 1:
            stddev = sqrt(float(reduce(lambda x, y: x + y, map(lambda x: (x - average) ** 2, values))) / (len(values) - 1))
        else:
            stddev = 0.0
        percent_stddev = (stddev / average) * 100.0
        print "%s_minimum %.3f" % (test_name, minimum)
        print "%s_maximum %.3f" % (test_name, maximum)
        print "%s_average %.3f" % (test_name, average)
        print "%s_maximum_error %.3f%%" % (test_name, max_err)
        print "%s_stddev %.3f" % (test_name, stddev)
        print "%s_percent_stddev %.3f" % (test_name, percent_stddev)

        if max_err > 5.0:
            print "FAIL: maximum error is greater than 5%"
            test_pass = False

        if test_pass:
            print "PASS: test passes specified performance thresholds"
            print

# vi:set ts=4 sw=4 expandtab syntax=python:
