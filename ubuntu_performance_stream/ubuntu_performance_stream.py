#
#
import os
import platform
import time
from autotest.client import test, utils

#
# Number of stream iterations
#
ntimes = 10

#
# Stream size and binary name
#
#stream_size = 2000000000
stream_size = 200000000
stream_bin = 'stream_mp'

#
# Number of test iterations to get min/max/average stats
#
test_iterations = 3


class ubuntu_performance_stream(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'gfortran',
            'libgomp1',
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
                        values[field] = chunks[2]
        return values

    def run_stream(self):
        fields = [ 'Copy', 'Scale', 'Add', 'Triad' ]
        values = {}
        stream_exe_path = os.path.join(self.srcdir, stream_bin)
        size = stream_size / 1000000
        test_pass = True

        for i in range(test_iterations):
            results = utils.system_output(stream_exe_path, retain_output=True)
            values[i] = self.get_stats(results, fields)

            print results

            print
            print "Test %d of %d:" % (i + 1, test_iterations)
            for field in fields:
                print "average_time_for_%s_%dM[%d] %s" % (field.lower(), size , i, values[i][field])

        #
        #  Compute min/max/average:
        #
        print
        print "Collated Performance Metrics:"
        for field in fields:
            v = [ float(values[i][field]) for i in values ]
            maximum = max(v)
            minimum = min(v)
            average = sum(v) / float(len(v))
            max_err = (maximum - minimum) / average * 100.0

            print
            print "stream_" + field.lower() + "_minimum %.5f" % (minimum)
            print "stream_" + field.lower() + "_maximum %.5f" % (maximum)
            print "stream_" + field.lower() + "_average %.5f" % (average)
            print "stream_" + field.lower() + "_maximum_error %.2f%%" % (max_err)

            if max_err > 5.0:
                print "FAIL: maximum error is greater than 5%"
                test_pass = False

        print
        if test_pass:
            print "PASS: test passes specified performance thresholds"

    def get_sysinfo(self):
        page_size = int(utils.system_output('getconf PAGE_SIZE', retain_output=True))
        pages_available = int(utils.system_output('getconf _AVPHYS_PAGES', retain_output=True))
        memory_available = float(page_size * pages_available)
        #
        # 4 arrays of 8 bytes per elemet
        #
        memory_required = float(4 * 8 * stream_size)

        print 'date_ctime "' + time.ctime() + '"'
        print 'date_ns %-30.0f' % (time.time() * 1000000000)
        print 'kernel_version ' + platform.uname()[2]
        print 'hostname ' + platform.node()
        print 'virtualization ' + utils.system_output('systemd-detect-virt || true', retain_output=True)
        print 'cpus_online ' + utils.system_output('getconf _NPROCESSORS_ONLN', retain_output=True)
        print 'cpus_total ' + utils.system_output('getconf _NPROCESSORS_CONF', retain_output=True)
        print 'page_size ', page_size
        print 'pages_availble ', pages_available
        print 'memory_available %.2f MB' % (memory_available / (1024 * 1024))
        print 'memory_required %.2f MB' % (memory_required / (1024 * 1024))
        print 'pages_total ' + utils.system_output('getconf _PHYS_PAGES', retain_output=True)
        print 'ntimes %d' % ntimes

        if memory_required > memory_available:
                print 'WARNING: Not enough memory available to run stream for %d elements without swapping, skipping test' % stream_size
		return False
	return True

    def run_once(self, test_name):
        if test_name == 'setup':
            return

        enough_ram = self.get_sysinfo()
        if enough_ram:
            print
            self.run_stream()
        print

# vi:set ts=4 sw=4 expandtab syntax=python:
