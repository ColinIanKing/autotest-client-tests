#
#
import os
import platform
import time
import subprocess
import resource
from autotest.client import test, utils

#
# Number of stream iterations
#
ntimes = 10

#
# Stream size and binary name
#
stream_bin = 'stream_mp'

if (os.uname()[1] == 'akis') or \
   ('TEST_CONFIG' in os.environ and 'config' in os.environ['TEST_CONFIG']):
    stream_size = 2000000000
else:
    stream_size = 200000000

#
# Number of test iterations to get min/max/average stats
#
test_iterations = 3


class ubuntu_performance_stream(test.test):
    version = 1
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
                    print("stopped service %s" % (service))
                else:
                    print("WARNING: could not stop %s" % (service))
        return stopped_services

    def start_services(self, services):
        for service in services:
            cmd = "%s start %s" % (self.systemctl, service)
            result = subprocess.Popen(cmd, shell=True)
            result.communicate()
            if result.returncode == 0:
                print("restarted service %s" % (service))
            else:
                print("WARNING: could not start %s" % (service))

    def set_rlimit_nofile(self, newres):
        oldres = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, newres)
        return oldres

    def restore_rlimit_nofile(self, res):
        resource.setrlimit(resource.RLIMIT_NOFILE, res)

    def set_cpu_governor(self, mode):
        cmd = "/usr/bin/cpupower frequency-set -g " + mode + " > /dev/null"
        result = subprocess.Popen(cmd, shell=True, stdout=None, stderr=None)
        result.communicate()
        if result.returncode != 0:
            print("WARNING: could not set CPUs to performance mode '%s'" % mode)

    def set_swap_on(self, swap_on):
        cmd = "/sbin/swapon -a" if swap_on else "/sbin/swapoff -a"
        result = subprocess.Popen(cmd, shell=True, stdout=None, stderr=None)
        result.communicate()
        if result.returncode != 0:
            print("WARNING: could not set swap %s" % ("on" if swap_on else "off"))

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'gfortran',
            'libgomp1',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        release = platform.release()

        pkgs = [
            'linux-tools-generic',
            'linux-tools-' + release
        ]
        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

        self.install_required_pkgs()
        self.job.require_gcc()
        stream_exe_path = os.path.join(self.srcdir, stream_bin)
        stream_src = os.path.join(self.bindir, 'stream.c')

        os.chdir(self.srcdir)

        cmd = 'gcc -fopenmp -D_OPENMP -DSTREAM_ARRAY_SIZE=%d -DNTIMES=%d -mcmodel=large %s -o %s' % (stream_size, ntimes, stream_src, stream_exe_path)
        self.results = utils.system_output(cmd, retain_output=True)

        utils.system_output('rm -f /etc/*/S99autotest || true', retain_output=True)

    def get_stats(self, results, fields):
        values = {}
        for line in results.splitlines():
            chunks = line.split()
            if len(chunks) > 2:
                for field in fields:
                    if chunks[0] == field + ':':
                        values[field] = {}
                        values[field]['average_rate'] = fields[field] / float(chunks[2])
                        values[field]['average_time'] = float(chunks[2])
        return values

    def run_stream(self):
        #
        #  Memory scaling factors, converting to MB/s to MiB/s
        #
        fields = {
            'Copy':  (15258.8 * 2.0 * 1024.0 * 1024.0) / 1000000.0,
            'Scale': (15258.8 * 2.0 * 1024.0 * 1024.0) / 1000000.0,
            'Add':   (15258.8 * 3.0 * 1024.0 * 1024.0) / 1000000.0,
            'Triad': (15258.8 * 3.0 * 1024.0 * 1024.0) / 1000000.0
        }
        stats = [ 'average_rate', 'average_time' ]
        values = {}
        stream_exe_path = os.path.join(self.srcdir, stream_bin)
        size = stream_size / 1000000
        test_pass = True

        if 'TEST_CONFIG' in os.environ:
            config = '_' + os.environ['TEST_CONFIG']
        else:
            config = ''


        for i in range(test_iterations):
            results = utils.system_output(stream_exe_path, retain_output=True)
            values[i] = self.get_stats(results, fields)

            print(results)

            print("")
            print("Test %d of %d:" % (i + 1, test_iterations))
            for field in fields:
                for stat in stats:
                    print("stream%s_%s_for_%s_%dM[%d] %f" % (config, stat, field.lower(), size , i, values[i][field][stat]))

        #
        #  Compute min/max/average:
        #
        print("")
        print("Collated Performance Metrics:")
        for field in fields:
            for stat in stats:
                v = [ values[i][field][stat] for i in values ]
                maximum = max(v)
                minimum = min(v)
                average = sum(v) / float(len(v))
                max_err = (maximum - minimum) / average * 100.0

                print("")
                print("stream%s_%s_%s_minimum %.5f" % (config, stat, field.lower(), minimum))
                print("stream%s_%s_%s_maximum %.5f" % (config, stat, field.lower(), maximum))
                print("stream%s_%s_%s_average %.5f" % (config, stat, field.lower(), average))
                print("stream%s_%s_%s_maximum_error %.2f%%" % (config, stat, field.lower(), max_err))
                if max_err > 5.0:
                    print("FAIL: maximum error is greater than 5%")
                    test_pass = False

        print("")
        if test_pass:
            print("PASS: test passes specified performance thresholds")

    def get_sysinfo(self):
        page_size = int(utils.system_output('getconf PAGE_SIZE', retain_output=True))
        pages_available = int(utils.system_output('getconf _AVPHYS_PAGES', retain_output=True))
        memory_available = float(page_size * pages_available)
        #
        # 4 arrays of 8 bytes per element
        #
        memory_required = float(4 * 8 * stream_size)

        print('date_ctime "' + time.ctime() + '"')
        print('date_ns %-30.0f' % (time.time() * 1000000000))
        print('kernel_version ' + platform.uname()[2])
        print('hostname ' + platform.node())
        print('virtualization ' + utils.system_output('systemd-detect-virt || true', retain_output=True))
        print('cpus_online ' + utils.system_output('getconf _NPROCESSORS_ONLN', retain_output=True))
        print('cpus_total ' + utils.system_output('getconf _NPROCESSORS_CONF', retain_output=True))
        print('page_size %d' % (page_size))
        print('pages_available %d' % (pages_available))
        print('memory_available %.2f MB' % (memory_available / (1024 * 1024)))
        print('memory_required %.2f MB' % (memory_required / (1024 * 1024)))
        print('pages_total ' + utils.system_output('getconf _PHYS_PAGES', retain_output=True))
        print('ntimes %d' % ntimes)
        print('stream_size %d' % stream_size)

        if memory_required > memory_available:
                print('WARNING: Not enough memory available to run stream for %d elements without swapping, skipping test' % stream_size)
		return False
	return True

    def run_once(self, test_name):
        if test_name == 'setup':
            return

        enough_ram = self.get_sysinfo()
        if enough_ram:
            print("")
            self.stopped_services = self.stop_services()
            self.oldres = self.set_rlimit_nofile((500000, 500000))
            self.set_cpu_governor('performance')
            self.set_swap_on(False)

            self.run_stream()

            self.set_swap_on(True)
            self.set_cpu_governor('powersave')
            self.set_rlimit_nofile(self.oldres)
            self.start_services(self.stopped_services)
        print("")

# vi:set ts=4 sw=4 expandtab syntax=python:
