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
test_iterations = 5

class ubuntu_performance_misc(test.test):
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
        pkgs = [ 'eventstat', 'forkstat' ]
        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()

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

    def parse_eventstat(self, output):
        for lines in output.splitlines():
            words = lines.split()
            if len(words) > 3 and words[1] == 'Total' and words[2] == 'events,':
                return float(words[3])
        return 0.0

    def parse_vmstat_generic(self, output, field):
	lines = output.splitlines()
	if len(lines) < 3:
		return 0.0
	words = lines[0].split()
	if field not in words:
		return 0.0
	idx = words.index(field)
	words = lines[2].split()
	if len(words) < idx:
		return 0.0
	return float(words[idx])

    def parse_vmstat_interrupts(self, output):
	return self.parse_vmstat_generic(output, 'in')

    def parse_vmstat_context_switches(self, output):
	return self.parse_vmstat_generic(output, 'cs')

    def parse_forks(self, output):
        forks = 0
        for line in output.splitlines():
            words = line.split()
            if len(words) > 3 and words[1] == 'fork' and  words[3] == 'child':
                forks = forks + 1
        return float(forks)

    def run_once(self, test_name):
        if test_name == 'setup':
            return self.get_sysinfo()

        if test_name == 'kernel-wakeups':
            cmd = 'sudo eventstat 60 1 -k'
            self.parser = self.parse_eventstat
        elif test_name == 'userspace-wakeups':
            cmd = 'sudo eventstat 60 1 -u'
            self.parser = self.parse_eventstat
	elif test_name == 'interrupts':
	    cmd = 'vmstat 60 2 -n  | grep -v ^procs'
            self.parser = self.parse_vmstat_interrupts
	elif test_name == 'context-switches':
	    cmd = 'vmstat 60 2 -n  | grep -v ^procs'
            self.parser = self.parse_vmstat_context_switches
	elif test_name == 'forks':
	    cmd = 'forkstat -D 60 -e fork | grep fork'
            self.parser = self.parse_forks
        else:
            return

        test_name = test_name.replace("-", "_")

        self.stopped_services = self.stop_services()
        self.oldres = self.set_rlimit_nofile((500000, 500000))

        results = []
        for i in range(test_iterations):
            output = utils.system_output(cmd, retain_output=True)
            results.append(self.parser(output))

        minimum = min(results)
        maximum = max(results)
        average = sum(results) / len(results)
        max_err = (maximum - minimum) / average * 100.0
        stddev = sqrt(float(reduce(lambda x, y: x + y, map(lambda x: (x - average) ** 2, results))) / (len(results) - 1))
        percent_stddev = (stddev / average) * 100.0 if average > 0.0 else 0.0

        print("")
        print("%s " % (test_name) + "%.3f " * len(results) % tuple(results))
        print("%s_minimum %.3f" % (test_name, minimum))
        print("%s_maximum %.3f" % (test_name, maximum))
        print("%s_average %.3f" % (test_name, average))
        print("%s_maximum_error %.3f%%" % (test_name, max_err))
        print("%s_stddev %.3f" % (test_name, stddev))
        print("%s_percent_stddev %.3f" % (test_name, percent_stddev))

        if max_err > 5.0:
            print("FAIL: maximum error is greater than 5%")
        else:
            print("PASS: test passes specified performance thresholds")

        self.set_rlimit_nofile(self.oldres)
        self.start_services(self.stopped_services)

        print("")

# vi:set ts=4 sw=4 expandtab syntax=python:
