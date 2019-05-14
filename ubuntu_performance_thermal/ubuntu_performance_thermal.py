#
#
import os
from autotest.client                        import test, utils
from math import sqrt
import platform

#
# Number of test iterations to get min/max/average stats
#
test_iterations = 3

class ubuntu_performance_thermal(test.test):
    version = 0

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

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        cmd = 'apt-get install zlib1g-dev libbsd-dev libattr1-dev libkeyutils-dev libapparmor-dev apparmor libaio-dev --assume-yes --allow-downgrades --allow-change-held-packages'
        utils.system_output(cmd, retain_output=True)
        os.chdir(self.srcdir)
        self.results = utils.system_output('git clone git://kernel.ubuntu.com/cking/stress-ng', retain_output=True)
        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        self.results = utils.system_output('git checkout -b V0.09.56 V0.09.56', retain_output=True)
        self.results = utils.system_output('make', retain_output=True)

    def parse(self, results, test_pass, test_full_name, field, name):
        for line in results.splitlines():
            chunks = line.split()
            if len(chunks) > 1 and chunks[0] == field:
                bogoops = [float(x) for x in chunks[1:]]
                minimum = min(bogoops)
                maximum = max(bogoops)
                average = sum(bogoops) / len(bogoops)
                max_err = (maximum - minimum) / average * 100.0

                if len(bogoops) > 1:
                    stddev = sqrt(float(reduce(lambda x, y: x + y, map(lambda x: (x - average) ** 2, bogoops))) / (len(bogoops) - 1))
                else:
                    stddev = 0.0
                percent_stddev = (stddev / average) * 100.0

                print
                print "%s_%s" % (test_full_name, name), "%.3f " * len(bogoops) % tuple(bogoops)
                print "%s_%s_minimum %.3f" % (test_full_name, name, minimum)
                print "%s_%s_maximum %.3f" % (test_full_name, name, maximum)
                print "%s_%s_average %.3f" % (test_full_name, name, average)
                print "%s_%s_maximum_error %.3f%%" % (test_full_name, name, max_err)
                print "%s_%s_stddev %.3f" % (test_full_name, name, stddev)
                print "%s_%s_percent_stddev %.3f" % (test_full_name, name, percent_stddev)

                if max_err > 5.0:
                    print "FAIL: maximum error is greater than 5%"
                    test_pass = False
        return test_pass

    def run_once(self, test_full_name, test_name, options, instances):
        if test_name == 'setup':
            return

        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        cmd = "%s/ubuntu_performance_thermal.sh '%s' '%s' %d %d" % (self.bindir, test_name, options, test_iterations, instances)
        self.results = utils.system_output(cmd, retain_output=True)

        test_name = test_name.replace("-", "_")
        test_full_name = test_full_name.replace("-", "_")

        test_pass = self.parse(self.results, True, test_full_name, 'PkgTemps:', 'x86_pkg_temp')
        test_pass = self.parse(self.results, test_pass, test_full_name, 'BogoOps:', 'bogoops')
        test_pass = self.parse(self.results, test_pass, test_full_name, 'BogoOpsPerKelvin:', 'bogoops_per_kelvin')
        if test_pass:
            print "PASS: test passes specified performance thresholds"
        print

# vi:set ts=4 sw=4 expandtab syntax=python:
