#
#
import os
from autotest.client                        import test, utils
from math import sqrt
import platform
import time

#
# Number of test iterations to get min/max/average stats
#
test_iterations = 3

percentage_threshold_slop=10

class ubuntu_performance_latency(test.test):
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

    def get_sysinfo(self):
        print 'date_ctime "' + time.ctime() + '"'
        print 'date_ns %-30.0f' % (time.time() * 1000000000)
        print 'kernel_version ' + platform.uname()[2]
        print 'hostname ' + platform.node()
        print 'virtualization ' + utils.system_output('systemd-detect-virt || true', retain_output=True)
        print 'cpus_online ' + utils.system_output('getconf _NPROCESSORS_ONLN', retain_output=True)
        print 'cpus_total ' + utils.system_output('getconf _NPROCESSORS_CONF', retain_output=True)
        print 'page_size ' + utils.system_output('getconf PAGE_SIZE', retain_output=True)
        print 'pages_available ' + utils.system_output('getconf _AVPHYS_PAGES', retain_output=True)
        print 'pages_total ' + utils.system_output('getconf _PHYS_PAGES', retain_output=True)

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

    def run_once(self, test_name):
        if test_name == 'setup':
            return self.get_sysinfo()

        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        cmd = '%s/ubuntu_performance_latency.sh %s %d' % (self.bindir, test_name, test_iterations)
        self.results = utils.system_output(cmd, retain_output=True)

        test_name = "latency_" + test_name.replace("-", "_")
        test_pass = True

        for field in ['mean', 'mode', 'min', 'max' ]:
            for line in self.results.splitlines():
                chunks = line.split()
                if len(chunks) > 1 and chunks[0] == field + ":":
                    value = float(chunks[1])
                    #
                    #  Just from a sample of 1 round of cyclic test, so average
                    #  is just from this one value. We need to append _average to
                    #  to named field so that the mass-scrape-influxdb.sh script
                    #  can scrape the field from the output and populate influxdb
                    #  with the data.
                    #
                    print "%s_%s_average %.3f" % (test_name, field, value)
        print

# vi:set ts=4 sw=4 expandtab syntax=python:
