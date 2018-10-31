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

percentage_threshold_slop=10

class ubuntu_performance_stress_ng(test.test):
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
        self.results = utils.system_output('git checkout -b V0.09.42 V0.09.42', retain_output=True)
        self.results = utils.system_output('make', retain_output=True)

    def run_once(self, test_name, threshold):
        if test_name == 'setup':
            return

        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        cmd = '%s/ubuntu_performance_stress_ng.sh %s %s %d' % (self.bindir, test_name, threshold, test_iterations)
        self.results = utils.system_output(cmd, retain_output=True)

        test_name = test_name.replace("-", "_")
        test_pass = True

        for line in self.results.splitlines():
            chunks = line.split()
            if len(chunks) > 1 and chunks[0] == 'BogoOps:':
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
                print "%s_bogoops" % (test_name), "%.3f " * len(bogoops) % tuple(bogoops)
                print "%s_minimum %.3f" % (test_name, minimum)
                print "%s_maximum %.3f" % (test_name, maximum)
                print "%s_average %.3f" % (test_name, average)
                print "%s_maximum_error %.3f%%" % (test_name, max_err)
                print "%s_stddev %.3f" % (test_name, stddev)
                print "%s_percent_stddev %.3f" % (test_name, percent_stddev)
                #print "%s_expected_threshold %.3f" % (test_name, threshold)
                #print "%s_within_threshold %s" % (test_name, percent_stddev < (threshold * (100 + percentage_threshold_slop) / 100.0))

                if max_err > 5.0:
                    print "FAIL: maximum error is greater than 5%"
                    test_pass = False

                if test_pass:
                    print "PASS: test passes specified performance thresholds"
		print

# vi:set ts=4 sw=4 expandtab syntax=python:
