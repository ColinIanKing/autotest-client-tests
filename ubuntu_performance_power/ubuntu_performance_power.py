#
#
import os
from autotest.client                        import test, utils
from math import sqrt
import platform
import time
import shutil
import subprocess
import resource

#
# Number of test iterations to get min/max/average stats
#
test_iterations = 5

class ubuntu_performance_power(test.test):
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
            'powerstat',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        os.chdir(self.srcdir)
        shutil.rmtree('stress-ng', ignore_errors=True)
        self.results = utils.system_output('git clone git://kernel.ubuntu.com/cking/stress-ng', retain_output=True)
        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        self.results = utils.system_output('git checkout -b V0.09.56 V0.09.56', retain_output=True)
        self.results = utils.system_output('make', retain_output=True)

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

    def parse(self, results, test_pass, test_full_name, field, name):
        for line in self.results.splitlines():
            chunks = line.split()
            if len(chunks) > 1 and chunks[0] == field:
                watts = [float(x) for x in chunks[1:]]
                minimum = min(watts)
                maximum = max(watts)
                average = sum(watts) / len(watts)
                max_err = (maximum - minimum) / average * 100.0

                if len(watts) > 1:
                    stddev = sqrt(float(reduce(lambda x, y: x + y, map(lambda x: (x - average) ** 2, watts))) / (len(watts) - 1))
                else:
                    stddev = 0.0
                percent_stddev = (stddev / average) * 100.0

                print("")
                print("%s_%s " % (test_full_name, name) + "%.3f " * len(watts) % tuple(watts))
                print("%s_%s_minimum %.3f" % (test_full_name, name, minimum))
                print("%s_%s_maximum %.3f" % (test_full_name, name, maximum))
                print("%s_%s_average %.3f" % (test_full_name, name, average))
                print("%s_%s_maximum_error %.3f%%" % (test_full_name, name, max_err))
                print("%s_%s_stddev %.3f" % (test_full_name, name, stddev))
                print("%s_%s_percent_stddev %.3f" % (test_full_name, name, percent_stddev))

                if max_err > 5.0:
                    print("FAIL: maximum error is greater than 5%")
                    test_pass = False
        return test_pass

    def run_once(self, test_full_name, test_name, options, instances):
        if test_name == 'setup':
            return self.get_sysinfo()

        self.stopped_services = self.stop_services()
        self.oldres = self.set_rlimit_nofile((500000, 500000))

        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        cmd = "%s/ubuntu_performance_power.sh '%s' '%s' %d %d" % (self.bindir, test_name, options, test_iterations, instances)
        self.results = utils.system_output(cmd, retain_output=True)

        test_name = test_name.replace("-", "_")
        test_pass = True
        test_full_name = test_full_name.replace("-", "_")

        test_pass = self.parse(self.results, True, test_full_name, 'Watts:', 'x86_watts')
        test_pass = self.parse(self.results, test_pass, test_full_name, 'BogoOps:', 'bogoops')
        test_pass = self.parse(self.results, test_pass, test_full_name, 'BogoOpsPerWatt:', 'bogoops_per_watt')
        if test_pass:
            print("PASS: test passes specified performance thresholds")
        print("")

        self.set_rlimit_nofile(self.oldres)
        self.start_services(self.stopped_services)

# vi:set ts=4 sw=4 expandtab syntax=python:
