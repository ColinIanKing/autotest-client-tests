#
#
import os
import re
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
releases = [ 'xenial', 'bionic', 'disco', 'eoan' ]

class ubuntu_performance_multipass(test.test):
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
                    print "WARNING: could not stop %s" % (service)
        return stopped_services

    def start_services(self, services):
        for service in services:
            cmd = "%s start %s" % (self.systemctl, service)
            result = subprocess.Popen(cmd, shell=True)
            result.communicate()
            if result.returncode != 0:
                print "WARNING: could not start %s" % (service)

    def set_rlimit_nofile(self, newres):
        oldres = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, newres)
        return oldres

    def restore_rlimit_nofile(self, res):
        resource.setrlimit(resource.RLIMIT_NOFILE, res)

    def initialize(self):
        pass

    def setup(self):
        cmd = 'sudo snap install multipass'
        self.results = utils.system_output(cmd, retain_output=True)

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

    #
    #  multipass_run_cmd - run a command, discard output and return True if it fails
    #
    def multipass_run_cmd(self, cmd):
        devnull = open(os.devnull, 'w')
        result = subprocess.Popen(cmd, shell=True, stdout=devnull, stderr=devnull)
        devnull.close()
        result.communicate()
        if result.returncode == 0:
            return False
        return True

    #
    #  wait for multipass to start and ensure we can exec commands
    #  on the instance once it is up and running. Return True if it
    #  fails.
    #
    def multipass_wait_for_start(self, vm):
        count = 0
        while count < 120:
		cmd = 'multipass list'
                results = utils.system_output(cmd, retain_output=True)
		for line in results.splitlines():
			if 'Running' in line and vm in line:
				count = 0
				while count < 60:
					cmd = 'multipass exec ' + vm + ' -- ps'
					if self.multipass_run_cmd(cmd) == 0:
						return False
					time.sleep(1)
					count = count + 1
				return True

		time.sleep(1)
		count = count + 1

	return True

    #
    #  run a command on a multipass instance named vm and return the output as
    #  a hunk of text
    #
    def multipass_run_cmd_output(self, vm, cmd):
	cmd = 'multipass exec ' + vm + ' -- ' + cmd
	return utils.system_output(cmd, retain_output=True)

    #
    #   look for text between str1 and str2 in line, extra times
    #   in seconds, milliseconds and minutes and total these up
    #   and return the time in seconds (float)
    #
    def parse_chunk(self, str1, str2, line):
	i = line.find(str1) + len(str1)
	j = line.find(str2)
        r_sec = re.compile(r'[-+]?([0-9]+s|[0-9]*\.[0-9]+s)')
        r_msec = re.compile(r'[-+]?([0-9]+ms|[0-9]*\.[0-9]+ms)')
        r_min = re.compile(r'[-+]?([0-9]+min|[0-9]*\.[0-9]+min)')
        t = 0.
	for str in line[i:j].split():
            if r_msec.match(str) != None:
                t = t + (float(str[0:str.find('ms')]) / 1000.0)
            if r_sec.match(str) != None:
                t = t + float(str[0:str.find('s')])
            if r_min.match(str) != None:
                t = t + (60.0 * float(str[0:str.find('min')]))
        return t

    #
    #  parse systemd_analyze output to get relevant times
    #
    def parse_systemd_analyze(self, results):
	kern = 0.0
	user = 0.0
	total = 0.0
	graphical = 0.0
        for line in results.splitlines():
            if 'Startup' in line:
                line = line + ' end'
                kern = self.parse_chunk('Startup finished in', '(kernel)', line)
                user = self.parse_chunk('+', '(userspace)', line)
                total = self.parse_chunk('=', 'end', line)
            if 'reached after' in line:
                graphical = self.parse_chunk('graphical.target reached after', 'in userspace', line + ' end')
        if kern > 0.0 and user > 0.0 and total > 0.0:
            return { 'kernel': kern, 'user': user, 'total': total, 'graphical': graphical }
        return None

    #
    #  boot, get systemd-analyze data and delete a multipass vm in a 'reliable'
    #  manner.  Returns None if it fails, otherwise and array containing the
    #  kernel info and an array of results of dictionaries containing
    #  kernel/user/total/graphical boot timings for the number of runs
    #
    def multipass_boot(self, vm, release):
        cmd = 'multipass launch -v -c 8 -m 1G -n ' + vm + ' daily:' + release
	if self.multipass_run_cmd(cmd):
		print("failed to launch")
                return None
	if self.multipass_wait_for_start(vm):
		print("failed to start")
                cmd = 'multipass delete ' + vm
		self.multipass_run_cmd(cmd)
                cmd = 'multipass purge'
	        self.multipass_run_cmd(cmd)
                return None

	results = self.multipass_run_cmd_output(vm, 'uname -r').splitlines()[0].split()
	if len(results) == 1:
		kernel = results[0]
	else:
		kernel = 'unknown'

	results = self.multipass_run_cmd_output(vm, 'systemd-analyze')
	stats = self.parse_systemd_analyze(results)

        cmd = 'multipass delete ' + vm
	if self.multipass_run_cmd(cmd):
		print("failed to delete VM " + vm)
        cmd = 'multipass purge'
	if self.multipass_run_cmd(cmd):
		print("failed to purge")
	return [ kernel, stats ]

    def run_once(self, test_name):
        if test_name == 'setup':
            return self.get_sysinfo()

        test_name = test_name.replace("-", "_")

        self.stopped_services = self.stop_services()
        self.oldres = self.set_rlimit_nofile((500000, 500000))

        for release in releases:
            kernel = 'unknown'
	    boot_results = []
            keys = []
            for i in range(test_iterations):
                [ kernel, result ] = self.multipass_boot('test', release)
                if result != None:
                     boot_results.append(result)
                     keys = keys + result.keys()

            keys = list(set(keys)) # find all unique keys in the results
            for key in keys:
                results = []
                for result in boot_results:
                    if key in result:
                        results.append(result[key])

                if len(results) > 0:
                    minimum = min(results)
                    maximum = max(results)
                    average = sum(results) / len(results)
                    if average > 0:
                        stddev = sqrt(float(reduce(lambda x, y: x + y, map(lambda x: (x - average) ** 2, results))) / (len(results) - 1))
                        percent_stddev = (stddev / average) * 100.0 if average > 0.0 else 0.0
                    else:
                        stddev = 0.0
                        percent_stddev = 0.0
                    print("%s_%s_%s_minimum %.3f" % (test_name, release, key, minimum))
                    print("%s_%s_%s_maximum %.3f" % (test_name, release, key, maximum))
                    print("%s_%s_%s_average %.3f" % (test_name, release, key, average))
                    print("%s_%s_%s_stddev %.3f" % (test_name, release, key, stddev))
                    print("%s_%s_%s_percent_stddev %.3f" % (test_name, release, key, percent_stddev))
                    print('')

        self.set_rlimit_nofile(self.oldres)
        self.start_services(self.stopped_services)

        print('')

# vi:set ts=4 sw=4 expandtab syntax=python:
