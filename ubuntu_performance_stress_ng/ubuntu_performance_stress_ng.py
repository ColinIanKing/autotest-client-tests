#
#
import os
from autotest.client                        import test, utils
from math import sqrt
import platform

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
        cmd = '%s/ubuntu_performance_stress_ng.sh %s %s' % (self.bindir, test_name, threshold)
        self.results = utils.system_output(cmd, retain_output=True)

	test_name = test_name.replace("-", "_")

        for line in self.results.splitlines():
            chunks = line.split()
            if len(chunks) > 1 and chunks[0] == 'BogoOps:':
                bogoops = [float(x) for x in chunks[1:]]
                mean = sum(bogoops) / len(bogoops)
                if len(bogoops) > 1:
                    stddev = sqrt(float(reduce(lambda x, y: x + y, map(lambda x: (x - mean) ** 2, bogoops))) / (len(bogoops) - 1))
		else:
                    stddev = 0.0
                percent_stddev = (stddev / mean) * 100.0
                print "%s_bogoops" % (test_name), "%.3f " * len(bogoops) % tuple(bogoops)
                print "%s_mean %.3f" % (test_name, mean)
                print "%s_stddev %.3f" % (test_name, stddev)
                print "%s_percent_stddev %.3f" % (test_name, percent_stddev)
                print "%s_expected_threshold %.3f" % (test_name, threshold)
                print "%s_within_threshold %s" % (test_name, percent_stddev < (threshold * (100 + percentage_threshold_slop) / 100.0))

# vi:set ts=4 sw=4 expandtab syntax=python:
