#
#
import os
from autotest.client                        import test, utils
from math import sqrt
import platform
import time
import subprocess
import resource

#
# Number of test iterations to get min/max/average stats
#
test_iterations = 3

percentage_threshold_slop=10

class ubuntu_performance_stress_ng(test.test):
    version = 0

    systemd_services = [
        "smartd.service",
        "iscsid.service",
        "apport.service",
        "cron.service",
        "anacron.timer",
        "apt-daily.timer",
        "apt-daily-upgrade.timer",
        "fstrim.timer",
        "logrotate.timer",
        "motd-news.timer",
        "man-db.timer",
    ]
    systemctl = "systemctl"

    def stop_services(self):
        stopped_services = []
        for service in self.systemd_services:
            cmd = "%s is-active --quiet %s" % (self.systemctl, service)
            result = subprocess.Popen(cmd, shell=True)
            result.communicate()
            if result.returncode == 0:
                cmd = "%s stop %s" % (self.systemctl, service)
                result = subprocess.Popen(cmd, shell=True)
                result.communicate()
                if result.returncode == 0:
                    stopped_services.append(service)
                else:
                    print("WARNING: could not stop %s" % (service))
        return stopped_services

    def start_services(self, services):
        for service in services:
            cmd = "%s start %s" % (self.systemctl, service)
            result = subprocess.Popen(cmd, shell=True)
            result.communicate()
            if result.returncode != 0:
                print("WARNING: could not start %s" % (service))

    def set_rlimit_nofile(self, newres):
        oldres = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, newres)
        return oldres

    def restore_rlimit_nofile(self, res):
        resource.setrlimit(resource.RLIMIT_NOFILE, res)

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'apparmor',
            'build-essential',
            'libaio-dev',
            'libapparmor-dev',
            'libattr1-dev',
            'libbsd-dev',
            'libkeyutils-dev',
            'zlib1g-dev'
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def get_sysinfo(self):
        print('date_ctime "' + time.ctime() + '"')
        print('date_ns %-30.0f' % (time.time() * 1000000000))
        print('kernel_version ' + platform.uname()[2])
        print('hostname ' + platform.node())
        print('virtualization ' + utils.system_output('systemd-detect-virt || true', retain_output=True))
        print('cpus_online ' + utils.system_output('getconf _NPROCESSORS_ONLN', retain_output=True))
        print('cpus_total ' + utils.system_output('getconf _NPROCESSORS_CONF', retain_output=True))
        print('page_size ' + utils.system_output('getconf PAGE_SIZE', retain_output=True))
        print('pages_available ' + utils.system_output('getconf _AVPHYS_PAGES', retain_output=True))
        print('pages_total ' + utils.system_output('getconf _PHYS_PAGES', retain_output=True))

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        os.chdir(self.srcdir)
        self.results = utils.system_output('git clone git://kernel.ubuntu.com/cking/stress-ng', retain_output=True)
        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        self.results = utils.system_output('git checkout -b V0.09.56 V0.09.56', retain_output=True)
        self.results = utils.system_output('make', retain_output=True)

    def run_once(self, test_name, threshold):
        if test_name == 'setup':
            return self.get_sysinfo()

        self.stopped_services = self.stop_services()
        self.oldres = self.set_rlimit_nofile((500000, 500000))

        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        cmd = '%s/ubuntu_performance_stress_ng.sh %s %s %d' % (self.bindir, test_name, threshold, test_iterations)
        self.results = utils.system_output(cmd, retain_output=True)

        self.set_rlimit_nofile(self.oldres)
        self.start_services(self.stopped_services)

        test_name = test_name.replace("-", "_")
        test_pass = True

        #print(self.results)

        for line in self.results.splitlines():
            chunks = line.split()
            if len(chunks) > 1 and chunks[0] == 'BogoOps:':
                bogoops = [float(x) for x in chunks[1:]]
                minimum = min(bogoops)
                maximum = max(bogoops)
                average = sum(bogoops) / len(bogoops)
                max_err = (maximum - minimum) / average * 100.0 if average > 0 else 0.0

                if len(bogoops) > 1:
                    stddev = sqrt(float(reduce(lambda x, y: x + y, map(lambda x: (x - average) ** 2, bogoops))) / (len(bogoops) - 1))
                else:
                    stddev = 0.0
                percent_stddev = (stddev / average) * 100.0 if average > 0 else 0.0
                print("")
                print("%s_bogoops " % (test_name) + "%.3f " * len(bogoops) % tuple(bogoops))
                print("%s_minimum %.3f" % (test_name, minimum))
                print("%s_maximum %.3f" % (test_name, maximum))
                print("%s_average %.3f" % (test_name, average))
                print("%s_maximum_error %.3f%%" % (test_name, max_err))
                print("%s_stddev %.3f" % (test_name, stddev))
                print("%s_percent_stddev %.3f" % (test_name, percent_stddev))
                #print("%s_expected_threshold %.3f" % (test_name, threshold))
                #print("%s_within_threshold %s" % (test_name, percent_stddev < (threshold * (100 + percentage_threshold_slop) / 100.0)))

                if max_err > 5.0:
                    print("FAIL: maximum error is greater than 5%")
                    test_pass = False

                if test_pass:
                    print("PASS: test passes specified performance thresholds")
                print("")

# vi:set ts=4 sw=4 expandtab syntax=python:
