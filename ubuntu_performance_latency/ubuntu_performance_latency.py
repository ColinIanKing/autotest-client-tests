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
test_iterations = 3

percentage_threshold_slop=10

class ubuntu_performance_latency(test.test):
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

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def get_sysinfo(self):
        print('date_ctime "' + time.ctime() + '"')
        print('date_ns %-30.0f' % (time.time() * 1000000000))
        print('kernel_version ' + platform.uname()[2])
        print('hostname ' + platform.node())
        print('virtualization ' + utils.system_output('systemd-detect-virt || true'))
        print('cpus_online ' + utils.system_output('getconf _NPROCESSORS_ONLN'))
        print('cpus_total ' + utils.system_output('getconf _NPROCESSORS_CONF'))
        print('page_size ' + utils.system_output('getconf PAGE_SIZE'))
        print('pages_available ' + utils.system_output('getconf _AVPHYS_PAGES'))
        print('pages_total ' + utils.system_output('getconf _PHYS_PAGES'))

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        os.chdir(self.srcdir)
        shutil.rmtree('stress-ng', ignore_errors=True)
        self.results = utils.system_output('git clone git://git.launchpad.net/~canonical-kernel-team/+git/stress-ng', retain_output=True)
        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        self.results = utils.system_output('git checkout -b V0.09.56 V0.09.56', retain_output=True)
        self.results = utils.system_output('patch -p1 < %s/0001-Add-build-time-check-for-struct-sockaddr_un.patch' % self.bindir, retain_output=True)
        self.results = utils.system_output('patch -p1 < %s/0002-stress-efivar-only-exercise-FS_IOC_-FLAGS-if-they-ar.patch' % self.bindir, retain_output=True)
        self.results = utils.system_output('patch -p1 < %s/0003-stress-ng.h-workaround-non-constant-stack-sizes-in-n.patch' % self.bindir, retain_output=True)
        self.results = utils.system_output('make', retain_output=True)

    def run_once(self, test_name):
        if test_name == 'setup':
            return self.get_sysinfo()

        self.stopped_services = self.stop_services()
        self.oldres = self.set_rlimit_nofile((500000, 500000))

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
                    print("%s_%s_average %.3f" % (test_name, field, value))
        print("")
        self.set_rlimit_nofile(self.oldres)
        self.start_services(self.stopped_services)


# vi:set ts=4 sw=4 expandtab syntax=python:
